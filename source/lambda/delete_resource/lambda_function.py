import boto3
import json
from datetime import datetime, timedelta
import logging
from utils.utils_aos import setup_opensearch_client, delete_opensearch_data
from utils.utils_s3 import delete_s3_objects, delete_folder
from utils.utils_dynamodb import delete_dynamodb_items

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    
    logger.info('delete_resource: {}'.format(event))
    
    # Extract user_id from the event
    user_id = event.get('user_id', 'user placeholder')
    
    # period = event.get('period', 'period placeholder')
    # if period == "all":
    #     days = 0
    # elif period == "1_day":
    #     days = 1
    # elif period == "3_days":
    #     days = 3
    # else:
    #     raise ValueError(f"Invalid period value: {period}")
    
    # Calculate the timestamp for x day ago
    days = event.get('period', 'period placeholder')
    x_day_ago = datetime.now() - timedelta(days=days)
    
    # Delete S3 objects
    delete_s3_objects(user_id, x_day_ago)
    
    # Delete DynamoDB items
    delete_dynamodb_items(user_id, x_day_ago)
    
    # Delete OpenSearch data
    delete_opensearch_data(user_id, x_day_ago)
    
    return {
        'statusCode': 200,
        'action': 'delete_resource',
        'body': json.dumps('Deletion process completed successfully')
    }
