import requests
import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests.auth import HTTPBasicAuth
from datetime import datetime
import os
import logging
from utils import setup_opensearch_client, get_titan_multimodal_embedding, get_presigned_url_from_uri, rerank_index, generate_conversation

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        logger.info('opensearch retrieve {}'.format(event))
            
        lambda_aos_client = setup_opensearch_client()

        user_id = event.get('user_id', "user_placeholder")
        keyword = event.get('keyword', "keyword_placeholder")
        timestamp_start = event.get('timestamp_start', None)
        timestamp_end = event.get('timestamp_end', None)
        search_count = event.get('search_count', 10)
        display_count = event.get('display_count', 10)

        if os.environ.get('PREPROCESS') == 'Y':
            model_id = "anthropic.claude-3-haiku-20240307-v1:0"
            query_message = keyword
            keyword = generate_conversation(model_id, query_message)
            print("update keyword", keyword)
        else:
            print("Skipping preprocessing")

        keyword_embedding = get_titan_multimodal_embedding(description=keyword, dimension=1024)["embedding"]

        query = {
            "size": display_count,
            "_source": ["image_url","description", "timestamp", "video_resource"],
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "user_id": user_id,
                            }
                        }, 
                        {
                            "knn": {
                                "image_vector": {
                                    "vector": keyword_embedding,
                                    "k": search_count
                                }
                            }
                        }
                    ]
                }
            }
        }

        if timestamp_start or timestamp_end:
                timestamp_range = {}
                if timestamp_start:
                    timestamp_range["gte"] = timestamp_start
                if timestamp_end:
                    timestamp_range["lte"] = timestamp_end
                
                query["query"]["bool"]["must"].append({
                    "range": {
                        "timestamp": timestamp_range
                    }
                })

        aos_response = lambda_aos_client.search(
            body = query,
            index = os.environ['INDEX_NAME']
        )

        results = []
        for hit in aos_response['hits']['hits']:
            results.append({
                "score": hit['_score'],
                "image_url": get_presigned_url_from_uri(hit['_source']['image_url']),
                "description": hit['_source']['description'],
                "timestamp": hit['_source']['timestamp'],
                "video_resource": hit['_source']['video_resource']
            })
            # print('description is', hit['_source']['description'])
        
        if os.environ.get('RERANK') == 'Y':
            new_index = rerank_index(results, keyword)
            print('new_index = ', new_index)
            final_results = [results[i] for i in new_index]
            results = final_results
        else:
            print('Skipping rerank process')

    except Exception as e:
        logger.error(f'Unexpected error occurred: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    return {
        'statusCode': 200,
        'action': 'opensearch_retrieve',
        'body': results
    }
    
