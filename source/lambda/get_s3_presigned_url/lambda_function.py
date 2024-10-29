import boto3
import os
import json
from botocore.exceptions import ClientError

# 创建S3客户端
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # 设置本地文件路径
    local_file_path = event['from_path']

    # 设置目标S3桶和文件夹
    bucket_name = event.get('bucket', os.environ['UPLOAD_BUCKET'])
    target_folder = event['to_path']

    # 生成目标文件路径
    target_file_path = os.path.join(target_folder, os.path.basename(local_file_path))
    
    # 设置Content-Type
    content_type = 'video/mp4'

    # 生成Presigned URL
    try:
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': bucket_name,
                'Key': target_file_path,
                'ContentType': content_type
            },
            ExpiresIn=600  # URL有效期为10分钟
        )
        print(presigned_url)
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    return {
        'statusCode': 200,
        'action': 'get_s3_presigned_url',
        'body': json.dumps({'s3_presigned_url': presigned_url})
    }
