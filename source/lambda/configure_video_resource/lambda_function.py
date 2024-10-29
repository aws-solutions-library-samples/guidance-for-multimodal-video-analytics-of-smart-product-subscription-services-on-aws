import os
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
ecs = boto3.client('ecs')
lambda_client = boto3.client('lambda')


def lambda_handler(event, context):
    logger.info('configure_video_resource: {}'.format(event))
    connection_id = event['connection_id']
    event = event['body']

    # video resource params
    user_id = event['user_id']
    video_source_type = event.get('video_source_type')
    video_source_content = event.get('video_source_content')

    if not video_source_type or not video_source_content or not user_id:
        return {
            'statusCode': 400,
            'body': 'Missing user_id or video_source_type or video_source_content in request'
        }

    # frame extraction params
    frequency = int(event.get('frequency', 10))
    list_length = int(event.get('list_length', 1))
    interval = float(event.get('interval', 1.0))
    duration = int(event.get('duration', 60))
    image_size = event.get('image_size', 'raw')

    # LLM params
    system_prompt = event.get('system_prompt', '')
    user_prompt = event.get('user_prompt', '')
    model_id = event.get('model_id', 'anthropic.claude-3-sonnet-20240229-v1:0')
    temperature = float(event.get('temperature', 0.1))
    top_p = float(event.get('top_p', 1))
    top_k = int(event.get('top_k', 250))
    max_tokens = int(event.get('max_tokens', 2048))

    # platform selection
    frame_extraction_platform = event.get('platform', 'lambda')

    if video_source_type == 's3_image':
        try:
            # construct request and invoke analysis lambda
            analysis_request = {
                'system_prompt': system_prompt,
                'user_prompt': user_prompt,
                'model_id': model_id,
                'temperature': temperature,
                'top_p': top_p,
                'top_k': top_k,
                'max_tokens': max_tokens,
                'image_path': video_source_content,
                'start_time': 0,
                'user_id': user_id,
                'task_id': event.get('task_id'),
                'video_source_type': video_source_type,
                'video_source_content': video_source_content,
                'connection_id': connection_id
            }

            logger.info(f'Analysis request: {analysis_request}')
            lambda_client.invoke(
                FunctionName=os.environ['VIDEO_ANALYSIS_LAMBDA'],
                InvocationType='Event',
                Payload=bytes(json.dumps(analysis_request), encoding='utf-8')
            )
        except Exception:
            logger.exception('Failed to invoke analysis lambda')
            return {
                'statusCode': 500,
                'body': 'Failed to invoke analysis lambda'
            }

        return {
            'statusCode': 200,
            'body': json.dumps({})
        }

    # retrieve default VPC with subnet list
    try:
        vpc = ec2.describe_vpcs(
            Filters=[
                {
                    'Name': 'is-default',
                    'Values': ['true']
                }
            ]
        ).get('Vpcs', [])[0]

        subnets = ec2.describe_subnets(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [vpc.get('VpcId')]
                }
            ]
        ).get('Subnets', [])

        subnet_ids = list(map(lambda x: x.get('SubnetId'), subnets))
    except Exception:
        logger.exception('Failed to get VPC subnets')
        return {
            'statusCode': 500,
            'body': 'Failed to get VPC subnets'
        }

    # frame_extraction_platform = os.environ['FRAME_EXTRACTION_PLATFORM']
    if frame_extraction_platform == 'ecs':
        # run ECS task
        try:
            ecs.run_task(
                cluster='frame_extraction_cluster',
                taskDefinition='frame-extraction-task',
                count=1,
                launchType='FARGATE',
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': subnet_ids,
                        'assignPublicIp': 'ENABLED'
                    }
                },
                overrides={
                    'containerOverrides': [
                        {
                            'name': 'frame_extraction',
                            'environment': [
                                {'name': 'connection_id', 'value': connection_id},
                                {'name': 'video_analysis_lambda', 'value': os.environ['VIDEO_ANALYSIS_LAMBDA']},
                                {'name': 'user_id', 'value': user_id},
                                {'name': 'video_source_type', 'value': video_source_type},
                                {'name': 'video_source_content', 'value': video_source_content},
                                {'name': 'video_upload_bucket_name', 'value': os.environ['VIDEO_UPLOAD_BUCKET_NAME']},
                                {'name': 'video_info_bucket_name', 'value': os.environ['VIDEO_INFO_BUCKET_NAME']},
                                {'name': 'frequency', 'value': str(frequency)},
                                {'name': 'list_length', 'value': str(list_length)},
                                {'name': 'interval', 'value': str(interval)},
                                {'name': 'duration', 'value': str(duration)},
                                {'name': 'image_size', 'value': image_size},
                                {'name': 'system_prompt', 'value': system_prompt},
                                {'name': 'user_prompt', 'value': user_prompt},
                                {'name': 'model_id', 'value': model_id},
                                {'name': 'temperature', 'value': str(temperature)},
                                {'name': 'top_p', 'value': str(top_p)},
                                {'name': 'top_k', 'value': str(top_k)},
                                {'name': 'max_tokens', 'value': str(max_tokens)}
                            ]
                        }
                    ]
                }
            )
        except Exception:
            logger.exception('Failed to run ECS task')
            return {
                'statusCode': 500,
                'body': 'Failed to run ECS task'
            }
    elif frame_extraction_platform == 'lambda':
        try:
            # construct request and invoke frame extraction lambda
            frame_extraction_request = {
                'connection_id': connection_id,
                'video_analysis_lambda': os.environ['VIDEO_ANALYSIS_LAMBDA'],
                'user_id': user_id,
                'video_source_type': video_source_type,
                'video_source_content': video_source_content,
                'video_upload_bucket_name': os.environ['VIDEO_UPLOAD_BUCKET_NAME'],
                'video_info_bucket_name': os.environ['VIDEO_INFO_BUCKET_NAME'],
                'frequency': str(frequency),
                'list_length': str(list_length),
                'interval': str(interval),
                'duration': str(duration),
                'image_size': image_size,
                'system_prompt': system_prompt,
                'user_prompt': user_prompt,
                'model_id': model_id,
                'temperature': str(temperature),
                'top_p': str(top_p),
                'top_k': str(top_k),
                'max_tokens': max_tokens,
            }

            # invoke frame extraction lambda
            logger.info(f'Frame extraction request: {frame_extraction_request}')
            lambda_client.invoke(
                FunctionName=os.environ['FRAME_EXTRACTION_LAMBDA'],
                InvocationType='Event',
                Payload=bytes(json.dumps(frame_extraction_request), encoding='utf-8')
            )
        except Exception:
            logger.exception('Failed to run lambda')
            return {
                'statusCode': 500,
                'body': 'Failed to run lambda'
            }

    return {
        'statusCode': 200,
        'body': json.dumps({})
    }
