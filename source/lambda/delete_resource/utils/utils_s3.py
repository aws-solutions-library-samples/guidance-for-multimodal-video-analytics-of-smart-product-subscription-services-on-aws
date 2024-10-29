import logging
import boto3
import json
import os
from datetime import datetime
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def delete_s3_objects(user_id, cutoff_date):
    s3 = boto3.client('s3')
    bucket_name = os.environ["UPLOAD_BUCKET"]
    
    logger.info(f"Starting deletion process for user: {user_id}, cutoff date: {cutoff_date}")
    
    # List only the direct subfolders under the user's folder
    response = s3.list_objects_v2(
        Bucket=bucket_name,
        Prefix=f'{user_id}/',
        Delimiter='/'
    )
    logger.debug(f"List objects response: {response}")
    
    # Process CommonPrefixes (which represent "folders")
    if 'CommonPrefixes' in response:
        for prefix in response['CommonPrefixes']:
            folder_name = prefix['Prefix'].split('/')[-2]  # Get the folder name
            logger.info(f"Processing folder: {folder_name}")
            
            if folder_name.startswith('task_'):
                try:
                    # Extract date from folder name
                    task_date = datetime.strptime(folder_name[5:19], '%Y-%m%d-%H%M%S')
                    logger.info(f"Task date: {task_date}")
                    
                    # Delete if older than cutoff date
                    if task_date < cutoff_date:
                        logger.info(f"Deleting folder: {prefix['Prefix']}")
                        delete_folder(s3, bucket_name, prefix['Prefix'])
                    else:
                        logger.info(f"Skipping folder (not old enough): {prefix['Prefix']}")
                except ValueError:
                    # Skip if folder name doesn't match expected format
                    logger.warning(f"Skipping folder due to unexpected format: {folder_name}")
                    continue
    else:
        logger.warning("No CommonPrefixes found in the response")

def delete_folder(s3_client, bucket, prefix):
    logger.info(f"Deleting contents of folder: {prefix}")
    
    # List and delete all objects within the folder
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

    delete_us = {
        'Objects': []
    }
    for page in pages:
        if "Contents" in page:
            for obj in page['Contents']:
                delete_us['Objects'].append({'Key': obj['Key']})
                logger.debug(f"Queueing object for deletion: {obj['Key']}")
        
        # Delete up to 1000 objects at a time (S3 limit)
        if len(delete_us['Objects']) >= 1000:
            logger.info(f"Deleting batch of {len(delete_us['Objects'])} objects")
            s3_client.delete_objects(Bucket=bucket, Delete=delete_us)
            delete_us = {'Objects': []}

    # Delete any remaining objects
    if delete_us['Objects']:
        logger.info(f"Deleting final batch of {len(delete_us['Objects'])} objects")
        s3_client.delete_objects(Bucket=bucket, Delete=delete_us)

    # Finally, delete the "folder" object itself if it exists
    logger.info(f"Attempting to delete folder object: {prefix}")
    s3_client.delete_object(Bucket=bucket, Key=prefix)
    
    logger.info(f"Finished deleting folder: {prefix}")