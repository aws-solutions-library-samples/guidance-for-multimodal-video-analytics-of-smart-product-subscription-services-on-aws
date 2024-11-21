import boto3
from datetime import datetime
import json
import logging
import os
from dynamodb_utils import query_dynamodb, create_xml
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# modelId = 'anthropic.claude-3-sonnet-20240229-v1:0'
modelId = 'anthropic.claude-3-haiku-20240307-v1:0'
#modelId = 'cohere.command-r-plus-v1:0'
#modelId = 'cohere.command-r-v1:0'
#modelId = 'mistral.mistral-large-2402-v1:0'
print(f'Using modelId: {modelId}')

bedrock = boto3.client(
    service_name = 'bedrock-runtime'
    )

class ToolsList:
    #Define our get_weather tool function...
    def send_notification(self, condition, message, receiver=None):
        print('in toolslist', condition, message, receiver)
        try:
            lambda_client = boto3.client('lambda')
            response = lambda_client.invoke(
                FunctionName=os.environ['TOOL_NOTIFICATION_LAMBDA'],
                InvocationType='Event',
                Payload=json.dumps(
                    {
                        "condition": condition,
                        "message": message,
                        "receiver": receiver
                    }
                    )
            )
        except Exception as e:
            logger.error(f'Error occurred while invoking Lambda function: {e}')
            raise e
        
        return json.dumps(response['Payload'].read().decode('utf-8'))
    
    def send_device_mqtt(self, command):
        print('in toolslist', command)
        try:
            lambda_client = boto3.client('lambda')
            response = lambda_client.invoke(
                FunctionName=os.environ['TOOL_DEVICE_LAMBDA'],
                InvocationType='Event',
                Payload=json.dumps(
                    {
                        "command": command
                    }
                    )
            )
        except Exception as e:
            logger.error(f'Error occurred while invoking Lambda function: {e}')
            raise e
        
        return json.dumps(response['Payload'].read().decode('utf-8'))
    
#Define the configuration for our tool...
toolConfig = {'tools': [],
'toolChoice': {
    'auto': {},
    #'any': {},
    #'tool': {
    #    'name': 'get_weather'
    #}
    }
}

toolConfig['tools'].append({
        'toolSpec': {
            'name': 'send_notification',
            'description': 'send mail to receiver when meet condition.',
            'inputSchema': {
                'json': {
                    'type': 'object',
                    'properties': {
                        'condition': {
                            'type': 'string',
                            'description': 'meet what condition to do action'
                        },
                        'message': {
                            'type': 'string',
                            'description': 'what message will be sent if meet condition'
                        },
                        'receiver': {
                            'type': 'string',
                            'description': 'the aws arn direction that the message will send. if no receiver, keep empty '
                        },
                    },
                    'required': ['condition', 'message']
                }
            }
        }
    })

toolConfig['tools'].append({
        'toolSpec': {
            'name': 'send_device_mqtt',
            'description': 'send command to control device.',
            'inputSchema': {
                'json': {
                    'type': 'object',
                    'properties': {
                        'command': {
                            'type': 'string',
                            'description': 'meet what condition to do action, format is json'
                        },
                    },
                    'required': ['command']
                }
            }
        }
    })

#Function for caling the Bedrock Converse API...
def converse_with_tools(messages, system='', toolConfig=toolConfig):
    response = bedrock.converse(
        modelId=modelId,
        system=system,
        messages=messages,
        toolConfig=toolConfig
    )
    return response

#Function for orchestrating the conversation flow...
def converse(prompt, system=''):
    #Add the initial prompt:
    messages = []
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "text": prompt
                }
            ]
        }
    )
    print(f"\n{datetime.now().strftime('%H:%M:%S')} - Initial prompt:\n{json.dumps(messages, indent=2)}")

    #Invoke the model the first time:
    output = converse_with_tools(messages, system)
    print(f"\n{datetime.now().strftime('%H:%M:%S')} - Output so far:\n{json.dumps(output['output'], indent=2, ensure_ascii=False)}")

    #Add the intermediate output to the prompt:
    messages.append(output['output']['message'])

    function_calling = next((c['toolUse'] for c in output['output']['message']['content'] if 'toolUse' in c), None)

    #Check if function calling is triggered:
    if function_calling:
        #Get the tool name and arguments:
        tool_name = function_calling['name']
        tool_args = function_calling['input'] or {}
        
        #Run the tool:
        print(f"\n{datetime.now().strftime('%H:%M:%S')} - Running ({tool_name}) tool...")
        tool_response = getattr(ToolsList(), tool_name)(**tool_args) or ""
        if tool_response:
            tool_status = 'success'
        else:
            tool_status = 'error'

        #Add the tool result to the prompt:
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        'toolResult': {
                            'toolUseId':function_calling['toolUseId'],
                            'content': [
                                {
                                    "text": tool_response
                                }
                            ],
                            'status': tool_status
                        }
                    }
                ]
            }
        )
        #print(f"\n{datetime.now().strftime('%H:%M:%S')} - Messages so far:\n{json.dumps(messages, indent=2)}")

        #Invoke the model one more time:
        output = converse_with_tools(messages, system)
        print(f"\n{datetime.now().strftime('%H:%M:%S')} - Final output:\n{json.dumps(output['output'], indent=2, ensure_ascii=False)}\n")
    return output['output']

def lambda_handler(event, context):
    
    user_id = event.get('user_id', 'userid_placeholder')
    task_id = event.get('task_id', 'task_placeholder')
    postprocess_prompt = event.get('agent_prompt', 'agent_placeholder')

    input_frame_result = query_dynamodb(user_id, task_id)
    query_result = create_xml(input_frame_result)

    record = query_result
    prompt_prefix = """Below is video analytics event results.\n"""
    postprocess_prompt = '\n<task>\n' + postprocess_prompt + '\n</task>' 
    
    final_input = prompt_prefix + record + postprocess_prompt


    prompts = [final_input]
    result =""
    for prompt in prompts:
        response = converse(
            system = [{"text": "You're provided with a tool that can send mail to receiver person or send command to device; \
                only use the tool if required. Don't make reference to the tools in your final answer."}],
            prompt = prompt
    )
        result = response
    output_result = result['message']['content'][0]['text']
    return {
        'statusCode': 200,
        'action': 'configure_agent',
        'body': json.dumps({'agent_result': output_result}, ensure_ascii=False)
    }
