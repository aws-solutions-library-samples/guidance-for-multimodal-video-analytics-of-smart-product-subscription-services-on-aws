import requests
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests.auth import HTTPBasicAuth
import boto3
import json
import os

# all cloudformation outputs
# region_name = os.environ.get('AWS_DEFAULT_REGION')
cloudformation = boto3.client('cloudformation')
stack_name = 'MultiModalVideoAnalyticsWebAppStack'
response = cloudformation.describe_stacks(StackName=stack_name)
outputs = response['Stacks'][0]['Outputs']

domain_endpoint = [output['OutputValue'] for output in outputs if output['OutputKey'] == 'opsdomain'][0]
api_id = [output['OutputValue'] for output in outputs if output['OutputKey'] == 'websocketapiid'][0]
table_name = [output['OutputValue'] for output in outputs if output['OutputKey'] == 'promptdatabase'][0]
lambda_name = [output['OutputValue'] for output in outputs if output['OutputKey'] == 'maillambda'][0]

email_address = input("Enter your postprocess notification email address (or press Enter to skip): ")

# 1.modify opensearch

secret_client = boto3.client('secretsmanager')
try:
    get_secret_value_response = secret_client.get_secret_value(
        SecretId='opensearch-master-user'
    )
except Exception as e:
    print(f'client error {e}')
    raise e

secret_string = get_secret_value_response['SecretString']
secret_dict = json.loads(secret_string)
# print(secret_dict["username"],"+",secret_dict["password"])


# headers = {"Content-Type": "application/json"}
host = domain_endpoint #<opensearch domain endpoint without 'https://'> #example: "opensearch-domain-endpoint.us-east-1.es.amazonaws.com"
# service = 'es'


# Use OpenSearch master credentials that you created while creating the OpenSearch domain
awsauth = HTTPBasicAuth(secret_dict["username"],secret_dict["password"])


#Initialise OpenSearch-py client
aos_client = OpenSearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    connection_class = RequestsHttpConnection
)

index_name = "multimodal-knn-index"
index_body = {
   "settings": {
      "index.knn": "true"
   },
   "mappings": {
      "properties": {
         "image_vector": {
            "type": "knn_vector",
            "dimension": 1024, # Embedding size for Amanon Titan Multimodal Embedding G1 model, it is 1,024 (default), 384, 256
            "method": {
                "name": "hnsw",
                "space_type": "l2",
                "engine": "faiss",
                "parameters": {
                "ef_construction": 128,
                "m": 24
                }
            }
         },
         "user_id": {"type": "keyword"},
         "timestamp" : {"type": "date"},
         "description": {"type": "text"},
         "image_url": {"type": "text"},
         "video_resource": {"type": "text"},
      }
   }
}

try:
    response = aos_client.indices.create(index_name, body=index_body)
    print(f"response received for the create index -> {response}")
except Exception as e:
    print(f"error in creating index={index_name}, exception={e}")
    
    
# 2.modify api gateway

try:
    apigw_client = boto3.client('apigatewayv2')
except Exception as e:
    print(f"An unexpected error occurred: {str(e)}")
# find apigateway matches requirements
integrations = apigw_client.get_integrations(
    ApiId=api_id,
)['Items']

target_integrations = []
for integration in integrations:
    uri = integration['IntegrationUri']
    if 'MultiModalVideoAnalytics' in uri and 'connect' not in uri and 'default' not in uri:
        target_integrations.append(integration)

# modify IntegrationType and create IntegrationResponse
for integration in target_integrations:
    integration_id = integration['IntegrationId']
    try:
        apigw_client.update_integration(
            ApiId=api_id,
            IntegrationId=integration_id,
            IntegrationType='AWS'
        )
    
        apigw_client.create_integration_response(
            ApiId=api_id,
            IntegrationId=integration_id,
            IntegrationResponseKey='$default',
            TemplateSelectionExpression="\\$default"
        )
        print(f'update integration type and response of {integration_id}')
    except Exception as e:
        print(f"Error updating integration type for {integration_id}: {e}")
        continue


# set RequestTemplates

cfg_js = '''
{
  "connection_id": "$context.connectionId",
  "body": $input.body
}
'''

for integration in target_integrations:
    uri = integration['IntegrationUri']
    if 'configure' in uri:
        integration_id = integration['IntegrationId']
        try:
            apigw_client.update_integration(
                ApiId=api_id,
                IntegrationId=integration_id,
                RequestTemplates={
                    "$default": cfg_js
                }
            )
            print(f'update integration request template of {integration_id}')
        except Exception as e:
            print(f"Error updating integration request template for {integration_id}: {e}")


# 3.modify prompt dynamodb
       
dynamodb = boto3.resource('dynamodb')

try:
    table = dynamodb.Table(table_name)
except Exception as e:
    print(f"Error getting table {table_name}: {e}")

system_prompt = '''
You are a helpful AI assistant.
<task>
You task is to describe the images.
</task>

Assistant:
'''

user_prompt = '''
You have perfect vision and pay great attention to detail which makes you an expert at traffic video monitor.
Before answering the question in <answer> tags, please think about it step-by-step within <thinking></thinking> tags
'''

item = {
    'user_id': 'public',
    'prompt_id': '6e2d7c5b-8f2d-4b7e-9f6f-8c1d2e3d4a5b',
    'industry_type': 'MFG',
    'topic_name': 'door-bell',
    'system_prompt': system_prompt,
    'user_prompt': user_prompt,

}
try:
    table.put_item(Item=item)
    print('Dynamodb items inserted successfully!')
except Exception as e:
    print(f"Error inserting item: {e}")
    raise

# 4.create sns and modify mail lambda configuration

sns_client = boto3.client('sns')
lambda_client = boto3.client('lambda')

# Function to create SNS topic and subscription

if not email_address:
    print("No email address provided. Skipping SNS topic creation.")
else:
    try:
        # Create SNS topic
        topic_response = sns_client.create_topic(Name='multimodal-mail')
        topic_arn = topic_response['TopicArn']

        # Subscribe to the topic
        subscription_response = sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email_address
        )

        # Set the SNS topic ARN as an environment variable for Lambda
        lambda_client.update_function_configuration(
            FunctionName=lambda_name,
            Environment={
                'Variables': {
                    'SNS_TOPIC_ARN': topic_arn
                }
            }
        )

        print(f"SNS topic created with ARN: {topic_arn}")
        print(f"Subscription created with ARN: {subscription_response['SubscriptionArn']}")
        print("Lambda environment variable 'SNS_TOPIC_ARN' updated with the SNS topic ARN.")
    except Exception as e:
        print(f"Error creating SNS topic or subscription: {e}")


