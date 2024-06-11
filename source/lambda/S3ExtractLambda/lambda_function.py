import boto3
import time
from datetime import datetime, timedelta
import cv2
import tempfile
import base64
import json
from io import BytesIO
import numpy as np

def lambda_handler(event, context):

    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')

    interval_time = event.get('interval', 2000)
    frequency = event.get('frequency',10)
    list_length = event.get('list_length',5)
    duration = event.get('duration',120)
    system_prompt = event.get('system_prompt', '你是一个图片阅读助手，请尽可能用中文详细得描述图片中的内容')
    user_prompt = event.get('user_prompt', '请描述图中的物品')
    
    # image_size = event.get('image_size', 'raw')
    image_size = 'raw'
    
    model_id = event.get('model_id','anthropic.claude-3-haiku-20240307-v1:0')
    temperature = event.get('temperature', 0.1)
    top_p = event.get('top_p', 1)
    top_k = event.get('top_k', 250)
    max_tokens = event.get('max_tokens', 2048)
    
    def maintain_image_list(lst, item, length=list_length):
        lst.append(item)
        if len(lst) > length:
            lst.pop(0)
            
    def resize_image(image_base64, target_size):
        
        image_data = base64.b64decode(image_base64)

        image_array = np.frombuffer(image_data, np.uint8)
        print('type of image_array is ', type(image_array))

        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        print('decode ok')

        width, height = map(int, target_size.split('*'))

        resized_image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)

        return resized_image

    def extract_frame(video, interval_time=2000, frequency=10):
        """
        This function simulates the analysis of video frames.
        It will analyze one frame per second and return the result.
        """
        cap = cv2.VideoCapture(video)
        fps = int(cap.get(5))
        print("fps=", fps)

        frame_interval = fps * int(interval_time/1000)
        print("frame_interval=", frame_interval)
        inference_interval = fps * frequency
        print("inference_interval=", inference_interval)
        frame_limit = duration*fps
        print("frame_limit=", frame_limit)

        frame_count = 0
        result = ""
        image_list_base64 = []

        while True:
            ret, frame = cap.read()
            frame_count += 1
            if ((not ret) or (frame_count>frame_limit)):
                now = datetime.now()
                current_timestamp = now.strftime("%Y-%m%d-%H%M%S")
                s3_client.put_object(Bucket='video-information-storage', Key=event['folder_name'] + '/' + current_timestamp +'_end', Body='END')
                break

            
            if frame_count % frame_interval == 0:
                # Simulate analysis
                _, buffer = cv2.imencode('.jpg', frame)
                frame_base64 = base64.b64encode(buffer).decode('utf8')
                maintain_image_list(image_list_base64, frame_base64)
                print("list ok, frame_count is ",frame_count)


            if frame_count % inference_interval == 0:
                now = datetime.now()
                current_timestamp = now.strftime("%Y-%m%d-%H%M%S")
                # raw_image_data = base64.b64decode(image_list_base64[-1])
                if image_size =='raw':
                    binary_image_data = base64.b64decode(image_list_base64[-1])
                    content = '\n'.join(item for item in image_list_base64)
                    print(len(image_list_base64))
                else:
                    binary_image_data = resize_image(image_list_base64[-1], image_size)
                s3_client.put_object(Bucket='video-information-storage', Key=event['folder_name'] + '/' + current_timestamp +'.jpg', Body=binary_image_data, ContentType='image/jpeg')
                s3_client.put_object(Bucket='video-information-storage', Key=event['folder_name'] + '/' + current_timestamp +'_img', Body=content.encode('utf-8'))

                response = lambda_client.invoke(
                    FunctionName = 'InvodeClaude3Lambda',
                    InvocationType='Event',
                    Payload=json.dumps(
                            {
                                "key": event['folder_name'] + '/' + current_timestamp,
                                "system_prompt": system_prompt,
                                "user_prompt": user_prompt,
                                "model_id": model_id,
                                "temperature": temperature,
                                "top_p": top_p,
                                "top_k": top_k,
                                "max_tokens": max_tokens
                                
                            })
                        )
                print("invoke ok, frame_count is ",frame_count)
                print(json.dumps(
                            {
                                "key": event['folder_name'] + '/' + current_timestamp,
                                "system_prompt": system_prompt,
                                "user_prompt": user_prompt,
                                "model_id": model_id,
                                "temperature": temperature,
                                "top_p": top_p,
                                "top_k": top_k,
                                "max_tokens": max_tokens
                                
                            }))

        cap.release()


    s3_client.download_file('video-upload-bucket', event['video_s3uri'], "/tmp/target.mp4")
    result = extract_frame("/tmp/target.mp4", interval_time, frequency)
