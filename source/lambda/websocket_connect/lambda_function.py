import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
connections = dynamodb.Table(os.environ['TABLE_NAME'])


def lambda_handler(event, context):
    logger.info('on connect: {}'.format(event))

    connection_id = event.get('requestContext', {}).get('connectionId')
    if not connection_id:
        return {
            'statusCode': 400,
            'body': 'Missing connection id in request'
        }

    result = connections.put_item(
        Item={
            'connectionId': connection_id
        }
    )
    if result.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
        logger.error('Fail to put connection id into DynamoDB: {}'.format(result))
        return {
            'statusCode': 500,
            'body': 'Fail to put connection id into DynamoDB'
        }

    return {
        'statusCode': 200,
        'body': connection_id
    }
