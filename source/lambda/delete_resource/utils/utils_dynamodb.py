import logging
from datetime import datetime
import boto3
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def delete_dynamodb_items(user_id, cutoff_date):
    logger.info(f"Starting DynamoDB deletion process for user: {user_id}, cutoff date: {cutoff_date}")
    
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ["RESULT_DYNAMODB"]
    table = dynamodb.Table(table_name)
    
    # Query items for the user
    logger.info(f"Querying DynamoDB for items belonging to user: {user_id}")
    response = table.query(
        KeyConditionExpression='user_id = :uid',
        ExpressionAttributeValues={':uid': user_id}
    )
    
    logger.info(f"Found {len(response['Items'])} items for user {user_id}")
    
    items_to_delete = 0
    for item in response['Items']:
        # Extract timestamp from the sort key
        sort_key = item['sort_key']
        try:
            task_date = datetime.strptime(sort_key[5:19], '%Y-%m%d-%H%M%S')
            logger.debug(f"Processing item with sort_key: {sort_key}, task_date: {task_date}")
            
            # Delete if older than cutoff date
            if task_date < cutoff_date:
                logger.info(f"Deleting item with sort_key: {sort_key}")
                table.delete_item(
                    Key={
                        'user_id': user_id,
                        'sort_key': sort_key
                    }
                )
                items_to_delete += 1
            else:
                logger.debug(f"Skipping item (not old enough): {sort_key}")
        except ValueError as e:
            logger.error(f"Error parsing date from sort_key: {sort_key}. Error: {str(e)}")
    
    logger.info(f"Deletion process completed. Deleted {items_to_delete} items for user {user_id}")