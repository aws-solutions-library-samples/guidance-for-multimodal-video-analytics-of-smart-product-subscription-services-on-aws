import json
import boto3
import time
from datetime import datetime, timedelta
import base64
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    kvs_client = boto3.client('kinesisvideo')
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    
    stream_name = event['kvs_stream']
    interval_time = event.get('interval', 1000)
    frequency = event.get('frequency',10)
    img_count = event.get('list_length',5)
    duration = event.get('duration', 60)
    system_prompt = event.get('system_prompt', '你是一个图片阅读助手，请尽可能用中文详细得描述图片中的内容')
    user_prompt = event.get('user_prompt', '请描述图中的物品')
    
    model_id = event.get('model_id','anthropic.claude-3-haiku-20240307-v1:0')
    temperature = event.get('temperature', 0.1)
    top_p = event.get('top_p', 1)
    top_k = event.get('top_k', 250)
    max_tokens = event.get('max_tokens', 2048)
    
    stop_flag = False
    cycle_limit = int(duration/frequency)
    cycle_count = 0
    gap_time = int(img_count*interval_time/1000)+5
    print("gap_time = ", gap_time)

        #get kvs information
    kvs_endpoint = kvs_client.get_data_endpoint(
        StreamName=stream_name,
        APIName='GET_IMAGES'
        ).get('DataEndpoint')
    kvs_image_client = boto3.client('kinesis-video-archived-media', endpoint_url = kvs_endpoint)
    
    hls_session = kvs_image_client.get_hls_streaming_session_url(
        StreamName=stream_name,
        Expires=43200,
        PlaybackMode='LIVE')
    
    # get AWS KVS HLS stream URL and write to s3 bucket folder
    hls_url = hls_session['HLSStreamingSessionURL']
    s3_client.put_object(Bucket='video-information-storage', Key=event['folder_name'] + '/' + 'hls', Body=hls_url)
    
    #start extract frames
    while not stop_flag:
        end_time = datetime.now()
        # start_time = end_time - timedelta(seconds=10)
        start_time = end_time - timedelta(seconds=gap_time)
    
        frame_response = kvs_image_client.get_images(
            StreamName=stream_name,
            ImageSelectorType='SERVER_TIMESTAMP',
            # MaxResults=5,
            SamplingInterval=interval_time,
            StartTimestamp=start_time,
            EndTimestamp=end_time,
            Format='JPEG'
            )
        image_contents_raw = [image['ImageContent'] for image in frame_response['Images'] if 'ImageContent' in image]
        
        #get img list on demand
        img_base64 = image_contents_raw[-1*img_count:]
        

        #write img to s3 bucket folder
        now = datetime.now()
        current_timestamp = now.strftime("%Y-%m%d-%H%M%S")
        
        # folder_name = 'kvs_extract_' + current_timestamp
        content = '\n'.join(item for item in img_base64)
        binary_image_data = base64.b64decode(img_base64[-1])
        s3_client.put_object(Bucket='video-information-storage', Key=event['folder_name'] + '/' + current_timestamp +'.jpg', Body=binary_image_data, ContentType='image/jpeg')
        s3_client.put_object(Bucket='video-information-storage', Key=event['folder_name'] + '/' + current_timestamp +'_img', Body=content.encode('utf-8'))
        

        #invode claude3
        response = lambda_client.invoke(
            FunctionName = 'InvodeClaude3Lambda',
            InvocationType='Event',
            Payload=json.dumps(
                    {
                        'key':event['folder_name'] + '/' + current_timestamp,
                        "system_prompt": system_prompt,
                        "user_prompt": user_prompt,
                        "model_id": model_id,
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k,
                        "max_tokens": max_tokens
                    })
                )

        cycle_count +=1
        if cycle_count > cycle_limit:
            now = datetime.now()
            current_timestamp = now.strftime("%Y-%m%d-%H%M%S")
            s3_client.put_object(Bucket='video-information-storage', Key=event['folder_name'] + '/' + current_timestamp +'_end', Body='END')
            break
        
        time.sleep(frequency)
    