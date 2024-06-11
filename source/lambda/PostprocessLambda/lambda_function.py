# -*- coding: utf-8 -*-
import boto3
import json
import re
from langchain_community.chat_models import BedrockChat
from langchain.agents import AgentExecutor, create_xml_agent
from agent_configs import prompt,tools

import time


def get_bucket_and_prefix(s3_uri):
    """
    Extracts the bucket name and prefix from an S3 URI.

    Args:
        s3_uri (str): The S3 URI in the format 's3://bucket_name/prefix/path'.

    Returns:
        tuple: A tuple containing the bucket name and prefix.
    """
    # Match the S3 URI pattern
    pattern = r's3://([^/]+)/?(.*)'
    match = re.match(pattern, s3_uri)

    if match:
        bucket_name = match.group(1)
        prefix = match.group(2)
        return bucket_name, prefix
    else:
        raise ValueError(f"Invalid S3 URI: {s3_uri}")
        

def read_files_with_substring(bucket_name, prefix, substring):
    s3 = boto3.client('s3')
    file_contents = '<event>\n'

    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    for obj in response.get('Contents', []):
        if substring in obj['Key']:
            obj_body = s3.get_object(Bucket=bucket_name, Key=obj['Key'])['Body'].read().decode('utf-8')
            file_contents += obj_body + '\n'
    
    file_contents += '</event>'
    
    return file_contents
    

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
)
model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

model_kwargs =  { 
    "max_tokens": 4096,
    "temperature": 0.1,
    "top_k": 250,
    "top_p": 1,
    "stop_sequences": ["\n\nHuman"],
}

model = BedrockChat(
    client=bedrock_runtime,
    model_id=model_id,
    model_kwargs=model_kwargs,
)

# Construct the XML Agent
agent = create_xml_agent(model, tools, prompt)

# Create an agent executor by passing in the agent and tools
agent_executor = AgentExecutor(agent=agent, tools=tools, return_intermediate_steps=True, verbose=True)


def lambda_handler(event, context):

    #------Check Input--------
    if 'result_s3uri' not in event.keys():
        print("result s3uri Not Input")
        return {
            'statusCode': 500,
            'body': json.dumps("Result S3uri Not Input")
        }
        
    if 'postprocess_prompt' not in event.keys():
        print("postprocess prompt Not Input")
        return {
            'statusCode': 500,
            'body': json.dumps("postprocess prompt Not Input")
        }
        
    s3uri = event['result_s3uri']
    postprocess_prompt = event['postprocess_prompt']
    
    #------ Build Input Prompt--------
    #s3://video-information-storage/s3_extract_2024-0417-055616/
    
    bucket_name, prefix = get_bucket_and_prefix(s3uri)
    print(f"Bucket Name: {bucket_name}")
    print(f"Prefix: {prefix}")
    substring = '.txt'
    
    start_time = time.time()
    record = read_files_with_substring(bucket_name, prefix, substring)
    
    prompt_prefix = """Below is video analytics event results.\n"""
    postprocess_prompt = '\n<task>\n' + postprocess_prompt + '\n</task>' 
    
    final_input = prompt_prefix + record + postprocess_prompt
    # final_input = event['user_input']
    print(final_input)
    
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"lada record execution_time: {execution_time} 秒")
    # # Invoke XML Agent
    
    try:
        start_time = time.time()
        response = agent_executor.invoke({"input": final_input})
        print(response['output'])
        print(response['intermediate_steps'][0][0])
        print(response['intermediate_steps'][0][1])
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"agent  execution_time: {execution_time} 秒")
        
        output = response['output']
        output = output.encode('utf-8')
    except Exception as e:
        print(e)
        
    
    return {
        'statusCode': 200,
        'body': output
    }
