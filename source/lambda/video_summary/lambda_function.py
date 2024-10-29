import boto3
from datetime import datetime
import json
import logging
from utils.dynamodb_utils import query_dynamodb, create_xml
from botocore.exceptions import ClientError
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def generate_conversation(bedrock_client,
                          model_id,
                          system_prompts,
                          messages, temperature, top_p, top_k, max_tokens):
    """
    Sends messages to a model.
    Args:
        bedrock_client: The Boto3 Bedrock runtime client.
        model_id (str): The model ID to use.
        system_prompts (JSON) : The system prompts for the model to use.
        messages (JSON) : The messages to send to the model.

    Returns:
        response (JSON): The conversation that the model generated.

    """

    logger.info("Generating message with model %s", model_id)

    # Inference parameters to use.
    # temperature = 0.5
    # top_k = 200

    # Base inference parameters to use.
    inference_config = {"temperature": temperature, "topP": top_p, "maxTokens": max_tokens}
    # Additional inference parameters to use.
    additional_model_fields = {"top_k": top_k}

    # Send the message.
    response = bedrock_client.converse(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields
    )

    # Log token usage.
    token_usage = response['usage']
    
    logger.info("Stop reason: %s", response['stopReason'])

    return response
    
def invoke_notify_lambda(notify_lambda_name, notify_request):
    """
    调用NotifyLambda函数
    :param notify_lambda_name: NotifyLambda函数名称
    :param notify_request: 请求参数
    """
    try:
        lambda_client = boto3.client('lambda')
        lambda_client.invoke(
            FunctionName=notify_lambda_name,
            InvocationType='Event',
            Payload=bytes(json.dumps(notify_request), encoding='utf-8')
        )
    except Exception as e:
        logger.error(f'Error occurred while invoking Lambda function: {e}')
        raise e

def lambda_handler(event, context):

    logger.info('vqa_chatbot: {}'.format(event))

    model_id = event.get('model_id', "anthropic.claude-3-sonnet-20240229-v1:0")
    temperature = event.get('temperature', 0.5)
    top_p = event.get('top_p', 1.0)
    top_k = event.get('top_k', 250)
    max_tokens = event.get('max_tokens', 2048)

    user_id = event.get('user_id', '6438b418-6041-7024-74e1-03a23aa99000')
    task_id = event.get('task_id', 'task_2024-0628-102005')
    connection_id = event.get('connection_id', '0001')
    postprocess_prompt = "pls summary the video content"

    input_frame_result = query_dynamodb(user_id, task_id)
    query_result = create_xml(input_frame_result)

    record = query_result
    prompt_prefix = """Below is video analytics event results.\n"""
    postprocess_prompt = '\n<task>\n' + postprocess_prompt + '\n</task>' 
    
    final_input = prompt_prefix + record + postprocess_prompt

    #Add the initial prompt:
    messages = []
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "text": final_input
                }
            ]
        }
    )

    system_prompts = [{"text": "You're an assisstant for video content summary."}]

    bedrock_client = boto3.client(service_name='bedrock-runtime')

    response = generate_conversation(
        bedrock_client, model_id, system_prompts, messages, temperature, top_p, top_k, max_tokens)

    output_message = response['output']['message']['content'][0]['text']
    print(output_message)
    
    notify_request = {
        "payload": {
            "summary_result": output_message,
            "task_id": task_id
        },
        "connection_id": connection_id
    }

    # 调用NotifyLambda
    invoke_notify_lambda(os.environ['NotifyLambda'], notify_request)

    return {
        'statusCode': 200,
        'body': json.dumps({'summary_result': output_message}, ensure_ascii=False)
    }