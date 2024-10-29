import json
import boto3
import xml.etree.ElementTree as ET
import time
import logging
import os
from botocore.exceptions import ClientError
from utils.dynamodb_utils import query_dynamodb, put_db, get_chat_history_db, create_xml
from utils.bedrock_utils import stream_conversation, _invoke_bedrock_with_retries, bedrock_claude_

logger = logging.getLogger()
logger.setLevel(logging.INFO)

CHAT_HISTORY_LENGTH = 5

dynamodb = boto3.resource('dynamodb')

query_table_name = os.environ["RESULT_DYNAMODB"]
query_table = dynamodb.Table(query_table_name)

chat_table_name = os.environ["HISTORY_DYNAMODB"]
chat_table = dynamodb.Table(chat_table_name)

bedrock_runtime = boto3.client(service_name='bedrock-runtime')

def conversation_bedroc_chat_(question, model_id, user_id, task_id):

    num_retries=0
    current_chat=[]
   
    # Retrieve past chat history from Dynamodb
    chat_histories = dynamodb.Table(chat_table_name).get_item(Key={"UserId": user_id, "SessionId":task_id})
    if "Item" in chat_histories:            
        current_chat,chat_hist=get_chat_history_db(chat_histories, CHAT_HISTORY_LENGTH)
    else:
        chat_hist=[]
    
    doc="I have provided documents"
    input_frame_result = query_dynamodb(user_id, task_id)
    query_result = create_xml(input_frame_result)
    doc+= query_result
    # print(doc)
    
    chat_template = 'you are an assistant'
    response,input_tokens,output_tokens=_invoke_bedrock_with_retries(current_chat, chat_template, doc+question, model_id)
    chat_history={"user":question,
    "assistant":response,
    "modelID":model_id,
    "time":str(time.time()),
    "input_token":round(input_tokens) ,
    "output_token":round(output_tokens)}         
                 
    #store convsation memory in DynamoDB table
    put_db(chat_history, user_id, task_id)

    return response

def lambda_handler(event, context):
    try:
        logger.info('vqa_chatbot: {}'.format(event))
        
        user_id = event['user_id']
        task_id = event['task_id']
        question = event['vqa_prompt']
        model_id = event.get('model', 'anthropic.claude-3-haiku-20240307-v1:0')

        response = conversation_bedroc_chat_(question, model_id, user_id, task_id)
        return {
            'statusCode': 200,
            'action': 'vqa_chatbot',
            'body': json.dumps({'vqa_result':response}, ensure_ascii=False)
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': str(e)
        }
