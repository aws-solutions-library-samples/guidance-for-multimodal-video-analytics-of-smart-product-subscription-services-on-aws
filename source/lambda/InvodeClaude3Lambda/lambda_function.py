import json
import logging
from pathlib import Path
import base64
import boto3
import time

from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def lambda_handler(event, context):

    bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')
    s3_client = boto3.client('s3')
    sqs_client = boto3.client('sqs')

    lambda_inference = event['key']
    lambda_system_prompt = event.get('system_prompt', '你是一个图片阅读助手，请尽可能用中文详细得描述图片中的内容')
    lambda_user_prompt = event.get('user_prompt', '请描述图中的物品')
    lambda_model_id = event.get('model_id','anthropic.claude-3-haiku-20240307-v1:0')
    lambda_temperature = event.get('temperature', 0.1)
    lambda_top_p = event.get('top_p', 1)
    lambda_top_k = event.get('top_k', 250)
    lambda_max_tokens = event.get('max_tokens', 2048)
    
    opensearch_ddb = event.get('opensearch_ddb', 'test_target')
    queue_url = "https://sqs.us-east-1.amazonaws.com/058264304798/standard-sqs"


    def run_multi_modal_prompt(bedrock_runtime, model_id, messages, max_tokens, system_prompt, temperature, top_p, top_k):
        """
        Invokes a model with a multimodal prompt.
        Args:
            bedrock_runtime: The Amazon Bedrock boto3 client.
            model_id (str): The model ID to use.
            messages (JSON) : The messages to send to the model.
            max_tokens (int) : The maximum  number of tokens to generate.
        Returns:
            None.
        """


        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k
            }
        )

        t0 = time.time()
        response = bedrock_runtime.invoke_model(body=body, modelId=model_id)
        response_body = json.loads(response.get('body').read())
        
        t1 = time.time()
        print("Invoke Cost: ",t1-t0)

        return response_body



    def call_claude3_img(input_text, input_image_paths=None, input_images=None, max_tokens=4000, system_prompt='你是一个图片阅读助手，请尽可能用中文详细得描述图片中的内容', model_id=lambda_model_id, temperature=0.1, top_p=1, top_k=250):
        """
        input_text: 输入的prompt
        input_image_paths & input_images: 图像的输入为list，输入为一组图像地址input_image_paths或者base64编码后的图像input_images，优先input_image_paths
        """

        try:
            
            if input_image_paths is not None:
                content_images = []
                
                if Path(input_image_paths).is_file():
                    with open(input_image_paths, "rb") as image_file:
                        content_images.append(base64.b64encode(image_file.read()).decode('utf8'))
                elif Path(input_image_paths).is_dir():
                    for input_image_path in input_image_paths:
                        with open(input_image_path, "rb") as image_file:
                            content_images.append(base64.b64encode(image_file.read()).decode('utf8'))
            else:
                content_images = input_images
                
            # content = [
            #     {
            #         "type": "image",
            #         "source":
            #         {
            #             "type": "base64",
            #             "media_type": "image/jpeg", 
            #             "data": content_image
            #         }
            #     }
                
            #     for idx, content_image in enumerate(content_images)
            # ]
            
            content = [
                [
                    {
                        "type": "text", 
                        "text": f"Image {i}"
                    },
                    {
                        "type": "image",
                        "source":
                        {
                            "type": "base64",
                            "media_type": "image/jpeg", 
                            "data": content_image
                        }
                    }
                ]
                for i, content_image in enumerate(content_images)
            ]
            content = [item for sublist in content for item in sublist]   
                
            # content text
            content.append({"type": "text", "text": input_text})
            message = {"role": "user",
                       "content": content}
            
            messages = [message]

            response = run_multi_modal_prompt(
                bedrock_runtime, model_id, messages, max_tokens, system_prompt, temperature, top_p, top_k)
            # print(response, type(response))
            # print(json.dumps(response, indent=4))
            return response['content'][0]['text']

        except ClientError as err:
            message = err.response["Error"]["Message"]
            logger.error("A client error occurred: %s", message)
            print("A client error occured: " +
                  format(message))
    
    def send_to_sqs(message_body):
    # 发送消息到SQS队列
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body
        )
        print(f'消息发送成功,消息ID: {response["MessageId"]}')

    #get image base64 from s3 bucket
    obj = s3_client.get_object(Bucket='video-information-storage', Key=event['key']+'_img')
    img_content = obj['Body'].read().decode('utf-8')
    img_base64 = img_content.split('\n')
    print("number of imgs: ",len(img_base64))


    #invoke claude3
    result = call_claude3_img(input_text=lambda_user_prompt, input_images=img_base64, max_tokens=lambda_max_tokens, system_prompt=lambda_system_prompt, model_id=lambda_model_id, temperature=lambda_temperature, top_p=lambda_top_p, top_k=lambda_top_k)
    # result = call_claude3_img(input_text="图里有哪些物体", input_images=img_base64)
    print(result)
    
    #write result to s3 & sqs
    s3_client.put_object(Bucket='video-information-storage', Key=event['key']+'.txt', Body=result)

    sqs_content = f'{opensearch_ddb}-{result}'
    send_to_sqs(sqs_content)

