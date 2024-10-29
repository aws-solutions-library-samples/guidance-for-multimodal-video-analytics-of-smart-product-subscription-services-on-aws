import os
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')


def lambda_handler(event, context):
    logger.info('get_s3_video_url: {}'.format(event))
    video_object_key = event.get('video_object_key')

    if not video_object_key:
        return {
            'statusCode': 400,
            'body': 'Missing video_object_key in request'
        }

    try:
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': os.environ['VIDEO_BUCKET_NAME'],
                'Key': video_object_key
            }
        )
        print(f'Video Play URL: {url}')
    except Exception:
        logger.exception('Failed to get S3 video url')
        return {
            'statusCode': 500,
            'body': 'Failed to get S3 video url'
        }

    return {
        'statusCode': 200,
        'action': 'get_s3_video_url',
        'body': json.dumps({
            's3_video_url': url
        })
    }
