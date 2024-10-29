import requests
import boto3
import json
import os
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests.auth import HTTPBasicAuth
from datetime import datetime
import logging
from utils import setup_opensearch_client, get_titan_multimodal_embedding

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        logger.info('opensearch ingest {}'.format(event))
        
        lambda_aos_client = setup_opensearch_client()

        user_id = event.get('user_id', "1234")
        description = event.get('result', "no description")
        path = event.get("img_url", "/")
        embedding_vector = get_titan_multimodal_embedding(image_path=path, dimension=1024)["embedding"]
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M')
        video_source_content = event.get("video_source_content", "videoname")

        index_name = os.environ['INDEX_NAME']  #"multimodal-knn-index"

        document = {
                    "user_id" : user_id,
                    "timestamp": timestamp,
                    "description": description,
                    "image_url": path,
                    "image_vector": embedding_vector,
                    "video_resource": video_source_content
                    }
        response = lambda_aos_client.index(
            index = index_name,
            body = document
        )
        
    except Exception as e:
        logger.error(f'Unexpected error occurred: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    return {
        'statusCode': 200,
        'body': response
    }
