import json
import boto3
import time
from datetime import datetime, timedelta

def lambda_handler(event, context):
    video_source_type = event["video_source_type"]

    interval = event.get('infer_frame_gap',1000)
    list_length = int(event.get('list_length',1))
    frequency = event.get('frequency',10)
    duration = event.get('duration',60)
    model_id = event.get('model_id','anthropic.claude-3-haiku-20240307-v1:0')
    temperature = event.get('temperature', 0.1)
    top_p = event.get('top_p', 1)
    top_k = event.get('top_k', 250)
    max_tokens = event.get('max_tokens', 2048)
    image_size = event.get('image_size', 'raw')

    
    #define environment, change bucket name for your own
    lambda_client = boto3.client('lambda')
    s3_client = boto3.client('s3')
    bucket_name = 'video-information-storage'
    
    #select route based on video_source_type
    if video_source_type == "s3":

        now = datetime.now()
        current_timestamp = now.strftime("%Y-%m%d-%H%M%S")
        folder_name = 's3_extract_' + current_timestamp
        s3_uri = f"s3://video-information-storage/{folder_name}/"
        s3_client.put_object(Bucket='video-information-storage', Key=folder_name + '/')

        response = lambda_client.invoke(
            FunctionName = "S3ExtractLambda",
            InvocationType="Event",
            Payload=json.dumps(
                {
                    "video_s3uri": event["video_s3uri"],
                    "interval": interval,
                    "list_length": list_length,
                    "frequency": frequency,
                    "system_prompt": event["system_prompt"],
                    "user_prompt": event["user_prompt"],
                    "duration": duration,
                    "folder_name": folder_name,
                    "model_id": model_id,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "max_tokens": max_tokens,
                    "image_size": image_size

                }
                )
            )
        print(json.dumps(
                {
                    "video_s3uri": event["video_s3uri"],
                    "interval": interval,
                    "list_length": list_length,
                    "frequency": frequency,
                    "system_prompt": event["system_prompt"],
                    "user_prompt": event["user_prompt"],
                    "duration": duration,
                    "folder_name": folder_name,
                    "model_id": model_id,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "max_tokens": max_tokens,
                    "image_size": image_size

                }))
        return {
            "statusCode": 200,
            "body":s3_uri
        }
    
    elif video_source_type == "camera":
        
        #create s3 bucket folder for each analytics operation
        now = datetime.now()
        current_timestamp = now.strftime("%Y-%m%d-%H%M%S")
        folder_name = 'kvs_extract_' + current_timestamp
        s3_uri = f"s3://video-information-storage/{folder_name}/"
        s3_client.put_object(Bucket='video-information-storage', Key=folder_name + '/')
        
        #extract frames with parameter interval/list_length/frequency
        response = lambda_client.invoke(
            FunctionName = "KVSExtractLambda",
            InvocationType="Event",
            Payload=json.dumps(
                {
                    "kvs_stream": event["camera_stream"],
                    "interval": interval,
                    "list_length": list_length,
                    "frequency": frequency,
                    "system_prompt": event["system_prompt"],
                    "user_prompt": event["user_prompt"],
                    "duration": duration,
                    "folder_name": folder_name,
                    "model_id": model_id,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "max_tokens": max_tokens,
                    "image_size": image_size
                }))
        return {
            "statusCode": 200,
            "body":s3_uri
        }
    
    #just for test        
    elif video_source_type == "echo":
        return {"statusCode": 200, "body": "test ok"}
        
    else:
        raise ValueError('Unrecognized operation "{}"'.format(video_source_type))
    