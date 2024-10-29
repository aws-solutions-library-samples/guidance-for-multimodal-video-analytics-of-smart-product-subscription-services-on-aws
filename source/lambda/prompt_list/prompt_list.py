import os
import json
import boto3
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['PROMPT_DYNAMODB']
table = dynamodb.Table(table_name)


def lambda_handler(event, context):
    # 处理预检请求
    if event['httpMethod'] == 'OPTIONS':
        response = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': '*'
            },
            'body': json.dumps({})
        }
        return response

    # 从查询字符串中获取 user_id
    user_id = event.get('queryStringParameters', {}).get('user_id', '').strip()

    # 验证输入
    if not user_id:
        response = {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': '*'
            },
            'body': json.dumps({
                'error': 'user_id is required and cannot be empty'
            })
        }
        return response

    public_response = table.query(
        KeyConditionExpression='user_id = :user_id',
        ExpressionAttributeValues={':user_id': 'public'},
        ProjectionExpression='prompt_id, topic_name, system_prompt, user_prompt, industry_type'
    )

    user_response = table.query(
        KeyConditionExpression='user_id = :user_id',
        ExpressionAttributeValues={':user_id': user_id},
        ProjectionExpression='prompt_id, topic_name, system_prompt, user_prompt, industry_type'
    )

    # 合并结果并添加 is_public 字段
    results = []
    for item in public_response['Items']:
        item['is_public'] = True
        results.append(item)

    for item in user_response['Items']:
        item['is_public'] = False
        results.append(item)

    response = {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': '*'
        },
        'body': json.dumps({
            'data': results
        })
    }
    return response