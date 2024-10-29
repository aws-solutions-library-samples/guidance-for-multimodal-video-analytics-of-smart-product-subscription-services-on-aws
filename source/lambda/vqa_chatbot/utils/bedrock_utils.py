import boto3
import logging
from botocore.exceptions import ClientError

bedrock_runtime = boto3.client(service_name='bedrock-runtime')

logger = logging.getLogger()

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

def stream_conversation(bedrock_client,
                    model_id,
                    messages,
                    system_prompts,
                    inference_config,
                    additional_model_fields):
    """
    Sends messages to a model and streams the response.
    Args:
        bedrock_client: The Boto3 Bedrock runtime client.
        model_id (str): The model ID to use.
        messages (JSON) : The messages to send.
        system_prompts (JSON) : The system prompts to send.
        inference_config (JSON) : The inference configuration to use.
        additional_model_fields (JSON) : Additional model fields to use.

    Returns:
        Nothing.

    """

    logger.info("Streaming messages with model %s", model_id)

    response = bedrock_client.converse_stream(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields
    )

    stream = response.get('stream')
    answer = ""
    input_tokens = 0
    output_tokens = 0
    
    if stream:
        for event in stream:

            # if 'messageStart' in event:
            #     print(f"\nRole: {event['messageStart']['role']}")

            if 'contentBlockDelta' in event:
                text = event['contentBlockDelta']['delta']['text']
                print(text, end="")
                
            #     notify_request = {
            #     "payload": {
            #         "analysis_result": text
            #     },
            #     "connection_id": connection_id
            # }
            #     # 调用NotifyLambda
            #     invoke_notify_lambda(os.environ['NotifyLambda'], notify_request)
                answer += str(text)

            # if 'messageStop' in event:
            #     print(f"\nStop reason: {event['messageStop']['stopReason']}")

            if 'metadata' in event:
                metadata = event['metadata']
                if 'usage' in metadata:
                    print("\nToken usage")
                    input_tokens = metadata['usage']['inputTokens']
                    output_tokens = metadata['usage']['outputTokens']
                    print("Input tokens: ", input_tokens)
                    print("Output tokens: ", output_tokens)
                if 'metrics' in event['metadata']:
                    print(
                        f"Latency: {metadata['metrics']['latencyMs']} ms")
                    
    return answer, input_tokens, output_tokens


def bedrock_claude_(chat_history,system_message, prompt,model_id):

    content=[]
    content.append({"text": prompt})
    chat_history.append({"role": "user",
            "content": content})

    system = [{'text':system_message}]

    inferenceConfig = {
    "maxTokens": 4096,
    "temperature": 0.5, 
    "topP": 1
    }
    
    additional_model_fields = {"top_k": 200}

    answer,input_tokens,output_tokens=stream_conversation(bedrock_runtime, model_id, chat_history,
                        system, inferenceConfig, additional_model_fields)

    return answer, input_tokens, output_tokens

def _invoke_bedrock_with_retries(current_chat, chat_template, question, model_id):
    max_retries = 5
    backoff_base = 2
    max_backoff = 3  # Maximum backoff time in seconds
    retries = 0

    while True:
        try:
            response,input_tokens,output_tokens= bedrock_claude_(current_chat, chat_template, question, model_id)
            return response,input_tokens,output_tokens
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if retries < max_retries:
                    # Throttling, exponential backoff
                    sleep_time = min(max_backoff, backoff_base ** retries + random.uniform(0, 1))
                    time.sleep(sleep_time)
                    retries += 1
                else:
                    raise e
            elif e.response['Error']['Code'] == 'ModelStreamErrorException':
                if retries < max_retries:
                    # Throttling, exponential backoff
                    sleep_time = min(max_backoff, backoff_base ** retries + random.uniform(0, 1))
                    time.sleep(sleep_time)
                    retries += 1
                else:
                    raise e
            elif e.response['Error']['Code'] == 'EventStreamError':
                if retries < max_retries:
                    # Throttling, exponential backoff
                    sleep_time = min(max_backoff, backoff_base ** retries + random.uniform(0, 1))
                    time.sleep(sleep_time)
                    retries += 1
                else:
                    raise e
            else:
                # Some other API error, rethrow
                raise