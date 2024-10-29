import os
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')


def lambda_handler(event, context):
    logger.info('list_s3_videos: {}'.format(event))
    user_id = event.get('user_id')

    if not user_id:
        return {
            'statusCode': 400,
            'body': 'Missing user_id in request'
        }

    try:
        response = s3.list_objects_v2(Bucket=os.environ['VIDEO_BUCKET_NAME'], Prefix=user_id)
        s3_videos = response.get('Contents', [])
    except Exception:
        logger.exception('Failed to list S3 video files')
        return {
            'statusCode': 500,
            'body': 'Failed to list S3 video files'
        }

    return {
        'statusCode': 200,
        'action': 'list_s3_videos',
        'body': json.dumps({
            's3_videos': s3_videos
        }, default=str)
    }
