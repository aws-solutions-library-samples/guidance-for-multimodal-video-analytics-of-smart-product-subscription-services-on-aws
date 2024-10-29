import boto3
from boto3.dynamodb.conditions import Key
import os

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['PROMPT_DYNAMODB']
table = dynamodb.Table(table_name)
public_user_id = os.environ['PUBLIC_USER'] 

def lambda_handler(event, context):
    user_ids = [event['user_id'], public_user_id]  # 包含两个 user_id 的列表

    # 初始化结果字典
    result = {}

    # 遍历 user_id 列表
    for user_id in user_ids:
        # 查询 DynamoDB 表,获取与给定 user_id 相关的项目
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )

        # 遍历查询结果,构建所需的数据结构
        for item in response['Items']:
            industry_type = item['industry_type']
            topic_name = item['topic_name']
            user_prompt = item['user_prompt']
            system_prompt = item['system_prompt']

            # 如果 industry_type 不存在于结果字典中,则创建一个新的字典
            if industry_type not in result:
                result[industry_type] = {}

            # 将 topic_name 及其对应的 user_prompt 和 system_prompt 添加到相应的 industry_type 字典中
            result[industry_type][topic_name] = {
                'user_prompt': user_prompt,
                'system_prompt': system_prompt
            }

    # 构建所需的响应格式
    response = {
        "action": "list_prompt",
        "payload": result
    }

    return response
    