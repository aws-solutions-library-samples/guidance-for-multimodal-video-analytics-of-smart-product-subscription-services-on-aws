import requests
import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests.auth import HTTPBasicAuth
from pathlib import Path
import base64
import os

session = boto3.session.Session()
region = session.region_name

# Define bedrock client
bedrock_client = boto3.client(
    "bedrock-runtime", 
    region, 
    endpoint_url=f"https://bedrock-runtime.{region}.amazonaws.com"
)


# Bedrock models
# Select Amazon titan-embed-image-v1 as Embedding model for multimodal indexing
multimodal_embed_model = f'amazon.titan-embed-image-v1'

"""
Function to generate Embeddings from image or text
"""

def get_titan_multimodal_embedding(
    image_path:str=None,  # maximum 2048 x 2048 pixels
    description:str=None, # English only and max input tokens 128
    dimension:int=1024,   # 1,024 (default), 384, 256
    model_id:str=multimodal_embed_model
):
    payload_body = {}
    embedding_config = {
        "embeddingConfig": { 
             "outputEmbeddingLength": dimension
         }
    }
    # You can specify either text or image or both
    if image_path:
        if image_path.startswith('s3'):
            s3 = boto3.client('s3')
            bucket_name, key = image_path.replace("s3://", "").split("/", 1)
            obj = s3.get_object(Bucket=bucket_name, Key=key)
            # Read the object's body
            body = obj['Body'].read()
            # Encode the body in base64
            base64_image = base64.b64encode(body).decode('utf-8')
            payload_body["inputImage"] = base64_image
        else:   
            with open(image_path, "rb") as image_file:
                input_image = base64.b64encode(image_file.read()).decode('utf8')
            payload_body["inputImage"] = input_image
    if description:
        payload_body["inputText"] = description

    if not payload_body:
        raise ValueError("Please provide either an image and/or a text description")
    # print("\n".join(payload_body.keys()))

    response = bedrock_client.invoke_model(
        body=json.dumps({**payload_body, **embedding_config}), 
        modelId=model_id,
        accept="application/json", 
        contentType="application/json"
    )

    return json.loads(response.get("body").read())




def setup_opensearch_client():
    # headers = {"Content-Type": "application/json"}
    host = os.environ["OPENSEARCH_ENDPOINT"] #<opensearch domain endpoint without 'https://'> #example: "opensearch-domain-endpoint.us-east-1.es.amazonaws.com"
    # service = 'es'
    # region = "us-east-1"

    # Use OpenSearch master credentials that you created while creating the OpenSearch domain
    secret_client = boto3.client('secretsmanager')
    try:
        get_secret_value_response = secret_client.get_secret_value(
            SecretId='opensearch-master-user'
        )
    except Exception as e:
        print(f"error in create opensearch client, exception={e}")
        raise e

    # 解码密钥值
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
