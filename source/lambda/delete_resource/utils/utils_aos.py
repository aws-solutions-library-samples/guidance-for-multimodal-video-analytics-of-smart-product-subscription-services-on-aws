import requests
import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests.auth import HTTPBasicAuth
from pathlib import Path
import base64
import os
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def setup_opensearch_client():
    # headers = {"Content-Type": "application/json"}
    host = os.environ["OPENSEARCH_ENDPOINT"] #<opensearch domain endpoint without 'https://'> #example: "opensearch-domain-endpoint.us-east-1.es.amazonaws.com"
    # Use OpenSearch master credentials that you created while creating the OpenSearch domain
    secret_client = boto3.client('secretsmanager')
    try:
        get_secret_value_response = secret_client.get_secret_value(
            SecretId='opensearch-master-user'
        )
    except Exception as e:
        print(f"error in create opensearch client, exception={e}")
        raise e

    secret_string = get_secret_value_response['SecretString']
    secret_dict = json.loads(secret_string)
    awsauth = HTTPBasicAuth(secret_dict["username"],secret_dict["password"])


    #Initialise OpenSearch-py client
    aos_client = OpenSearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        connection_class = RequestsHttpConnection
    )
    
    return aos_client
    
def delete_opensearch_data(user_id, cutoff_date):

    logger.info("Initializing OpenSearch client")
    
    aos_client = setup_opensearch_client()
    
    logger.info(f"Starting OpenSearch deletion process for user: {user_id}, cutoff date: {cutoff_date}")
    # Delete documents older than cutoff date
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"user_id": user_id}},
                    {"range": {"timestamp": {"lt": cutoff_date.isoformat()}}}
                ]
            }
        }
    }
    
    logger.info(f"Executing delete_by_query for user {user_id}")
    logger.debug(f"Delete query: {query}")

    try:
        response = aos_client.delete_by_query(index=os.environ['INDEX_NAME'], body=query)
        logger.info(f"Delete operation completed. Response: {response}")
        
        if 'deleted' in response:
            logger.info(f"Successfully deleted {response['deleted']} documents for user {user_id}")
        else:
            logger.warning(f"Unexpected response format. Full response: {response}")
    
    except Exception as e:
        logger.error(f"Error occurred while deleting documents: {str(e)}")
        raise

    logger.info(f"OpenSearch deletion process completed for user {user_id}")