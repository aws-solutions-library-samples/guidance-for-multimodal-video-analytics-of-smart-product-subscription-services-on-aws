import json
import logging
import boto3
import os
from pathlib import Path
import base64
import time
from botocore.exceptions import ClientError
import uuid
import shutil
from decimal import Decimal
from datetime import datetime
from multimodal_config import call_claude3_img

logger = logging.getLogger()
logger.setLevel(logging.INFO)
# 创建S3客户端
s3 = boto3.client('s3')

def download_files_from_s3(bucket_name, folder_path):
    """
    下载S3 Bucket中指定文件夹下的所有文件到临时目录
    :param bucket_name: S3 Bucket名称
    :param folder_path: 要下载的文件夹路径
    :return: 下载文件所在的临时目录路径,第一个对象的URI
    """
    try:
        
        # 创建用于存储下载文件的目录
        random_id = str(uuid.uuid4())[:8]  # 生成一个8位的随机字符串
        download_dir = f'/tmp/downloaded_images_{random_id}'
        os.makedirs(download_dir, exist_ok=True)

        # 列出要下载的文件
        objects = s3.list_objects(Bucket=bucket_name, Prefix=folder_path)
        
        first_object_key = None

        # 获取第一个对象的键
        if 'Contents' in objects and objects['Contents']:
            first_object_key = objects['Contents'][0]['Key']
            first_object_uri = f"s3://{bucket_name}/{first_object_key}"
            print(f"First object URI: {first_object_uri}")

        # 下载文件
        for obj in objects.get('Contents', []):
            key = obj['Key']
            target = os.path.join(download_dir, key[len(folder_path)+1:])
            print(f'Downloading: {key} to {target}')

            s3.download_file(bucket_name, key, target)
            print(f'Downloaded: {key}')

        return download_dir, first_object_key, first_object_uri

    except ClientError as e:
        logger.error(f'Error occurred while accessing S3: {e}')
        raise e
    except Exception as e:
        logger.error(f'Unexpected error occurred: {e}')
        raise e
        
def get_presigned_url(bucket_name, key):
    try:
        expiration = 600
        # 生成预签名URL
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': bucket_name,
                'Key': key,
                'ResponseContentType': 'image/jpeg'
            },
            ExpiresIn=expiration
        )
        print(f"预签名URL: {url}")
        return url
        
    except ClientError as e:
        print(f"Error: {e.response['Error']['Message']}")

def invoke_notify_lambda(notify_lambda_name, notify_request):
    """
    调用NotifyLambda函数
    :param notify_lambda_name: NotifyLambda函数名称
    :param notify_request: 请求参数
    """
    try:
        lambda_client = boto3.client('lambda')
        lambda_client.invoke(
            FunctionName=notify_lambda_name,
            InvocationType='Event',
            Payload=bytes(json.dumps(notify_request), encoding='utf-8')
        )
    except Exception as e:
        logger.error(f'Error occurred while invoking Lambda function: {e}')
        raise e
        
def invoke_summary_lambda(summary_lambda_name, model_id, temperature, top_p, top_k, max_tokens, user_id, task_id, connection_id):
    """
    调用SummaryLambda函数
    """
    try:
        lambda_client = boto3.client('lambda')
        summary_request = {
            "model_id": model_id,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_tokens": max_tokens,
            "user_id": user_id,
            "task_id": task_id,
            "connection_id": connection_id
        }
        lambda_client.invoke(
            FunctionName=summary_lambda_name,
            InvocationType='Event',
            Payload=bytes(json.dumps(summary_request), encoding='utf-8')
        )
    except Exception as e:
        logger.error(f'Error occurred while invoking Lambda function: {e}')
        raise e

def put_item_to_dynamodb(table, user_id, task_id, task_object, timestamp, folder_path, result):
    """
    将结果写入DynamoDB
    :param table: DynamoDB表
    :param user_id: 用户ID
    :param task_id: 任务ID
    :param task_object: 任务对象
    :param timestamp: 时间戳
    :param folder_path: 文件夹路径
    :param result: 分析结果
    """
    try:
        sort_key = f"{task_id}#{timestamp}"
        item = {
            'user_id': user_id,
            'sort_key': sort_key,
            'task_id': task_id,
            'task_object': task_object,
            'video_time': timestamp,
            'folder_path': folder_path,
            'frame_result': result
        }
        table.put_item(Item=item)
        logger.info(f"Successfully wrote item to DynamoDB: {item}")
    except ClientError as e:
        logger.error(f"Error occurred while writing to DynamoDB: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error occurred while writing to DynamoDB: {e}")
        raise e

def lambda_handler(event, context):
    try:
        logger.info('video_analysis: {}'.format(event))


        # 从event中获取参数
        bucket_name = event.get('bucket', os.environ['RESULT_BUCKET'])
        folder_path = event['image_path']
        timestamp = event.get('start_time', '00:00')
        connection_id = event.get('connection_id', 'connection_placeholder')
        user_id = str(event.get('user_id', 'id_placeholder'))
        task_id = str(event.get('task_id', 'task_placeholder'))
        task_object = event.get('video_source_content', 's3_placeholder')
        video_source_content = event.get('video_source_content','video_content')

        input_text = event.get('user_prompt', 'tell me the content of image in 30 words')
        system_prompt = event.get('system_prompt', 'you are an assistant')
        model_id = event.get('model_id', 'anthropic.claude-3-haiku-20240307-v1:0')
        temperature = event.get('temperature', 0.5)
        top_p = event.get('top_p', 1.0)
        top_k = event.get('top_k', 250)
        max_tokens = event.get('max_tokens', 2048)
        tag = event.get('tag', 'running')

        # 下载文件
        download_dir, first_object_key, first_object_uri = download_files_from_s3(bucket_name, folder_path)

        # 调用Claude3进行分析
        input_image_paths = Path(download_dir)
        print(f'Input image paths: {input_image_paths}')
        print(f'input_text={input_text}, system_prompt={system_prompt}, model_id={model_id}, temperature={temperature}, top_p={top_p}, top_k={top_k}, input_image_paths={input_image_paths}')
        result = call_claude3_img(input_text=input_text, system_prompt=system_prompt, model_id=model_id, temperature=temperature, top_p=top_p, top_k=top_k, input_image_paths=input_image_paths)
        print(result)

        # 删除下载目录
        shutil.rmtree(download_dir)

        # 准备调用NotifyLambda的请求参数
        first_object_presigned_url = get_presigned_url(bucket_name, first_object_key)
        if tag == 'end':            
            notify_request = {
                "payload": {
                    "timestamp": timestamp,
                    "img_url": first_object_presigned_url,
                    "analysis_result": result,
                    "task_id": task_id,
                    "tag": "end"
                },
                "connection_id": connection_id
            }
        else:
            notify_request = {
                "payload": {
                    "timestamp": timestamp,
                    "img_url": first_object_presigned_url,
                    "analysis_result": result,
                    "task_id": task_id
                },
                "connection_id": connection_id
            }

        # 调用NotifyLambda
        invoke_notify_lambda(os.environ['NOTIFY_LAMBDA'], notify_request)

        # 写入DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ['RESULT_DYNAMODB']
        table = dynamodb.Table(table_name)
        put_item_to_dynamodb(table, user_id, task_id, task_object, timestamp, folder_path, result)

        # call opensearch lambda
        ingest_payload = {
            "img_url": first_object_uri,
            "result": result,
            "user_id": user_id,
            "video_source_content": video_source_content,
        }
        invoke_notify_lambda(os.environ['OPS_INGEST_LAMBDA'], ingest_payload)

        # 在end时进行总结
        if tag == 'end':
            invoke_summary_lambda(
                os.environ['SUMMARY_LAMBDA'],
                model_id,
                temperature,
                top_p,
                top_k,
                max_tokens,
                user_id,
                task_id,
                connection_id
            )

    except Exception as e:
        logger.error(f'Unexpected error occurred: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    return {
        'statusCode': 200,
        'body': result
    }
    