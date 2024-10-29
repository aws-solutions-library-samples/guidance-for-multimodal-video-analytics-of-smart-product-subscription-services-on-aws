import os
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info('websocket_notify: {}'.format(event))
    payload = event.get('payload')
    connection_id = event.get('connection_id')

    if not payload or not connection_id:
        return {
            'statusCode': 400,
            'body': 'Missing payload or connection_id in request'
        }

    # Create an ApiGatewayManagementApi client
    apigatewaymanagementapi = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['ENDPOINT_URL'])

    # Send the message to the WebSocket connection
    payload.update({"action": "websocket_notify"})
    try:
        apigatewaymanagementapi.post_to_connection(
            Data=json.dumps(payload).encode(),
            ConnectionId=connection_id
        )
    except Exception:
        logger.exception('Fail to send message to WebSocket connection')
        return {
            'statusCode': 500,
            'body': 'Fail to send message to WebSocket connection'
        }

    return {
        'statusCode': 200,
        'body': json.dumps({})
    }
