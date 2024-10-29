import os
import json
import uuid
import boto3

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['PROMPT_DYNAMODB']
table = dynamodb.Table(table_name)

def options_handler(event):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': '*'
        },
        'body': json.dumps({})
    }

def lambda_handler(event, context):
    print(event)
    http_method = event['httpMethod']
    print(http_method)
    if http_method == 'OPTIONS':
        return options_handler(event)
    if http_method == 'POST':
        try:
            body = json.loads(event['body'])
        except (ValueError, KeyError):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': '*'
                },
                'body': json.dumps({'error': 'Invalid request body'})
            }
        return create_prompt(body)
    elif http_method == 'PUT':
        try:
            body = json.loads(event['body'])
        except (ValueError, KeyError):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': '*'
                },
                'body': json.dumps({'error': 'Invalid request body'})
            }
        return update_prompt(body)
    elif http_method == 'DELETE':
        try:
            body = json.loads(event['body'])
            print(body, "000")
        except (ValueError, KeyError):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': '*'
                },
                'body': json.dumps({'error': 'Invalid request body'})
            }
        return delete_prompt(body)
    else:
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': '*'
            },
            'body': json.dumps({'error': 'Method Not Allowed'})
        }

def create_prompt(body):
    user_id = body.get('user_id', '').strip()
    topic_name = body.get('topic_name', '').strip()
    industry_type = body.get('industry_type', '').strip()
    system_prompt = body.get('system_prompt', '').strip()
    user_prompt = body.get('user_prompt', '').strip()
    print(user_id)
    print(topic_name)
    print(industry_type)
    print(system_prompt)
    print(user_prompt)

    if not user_id or not topic_name or not industry_type or not system_prompt or not user_prompt:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': '*'
            },
            'body': json.dumps({'error': 'Missing required parameters'})
        }

    prompt_id = str(uuid.uuid4())

    table.put_item(
        Item={
            'user_id': user_id,
            'prompt_id': prompt_id,
            'topic_name': topic_name,
            'industry_type': industry_type,
            'system_prompt': system_prompt,
            'user_prompt': user_prompt
        }
    )

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': '*'
        },
        'body': json.dumps({
            'message': 'Creation successful',
            'data': {'prompt_id': prompt_id}
        })
    }

def update_prompt(body):
    user_id = body.get('user_id', '').strip()
    prompt_id = body.get('prompt_id', '').strip()
    if not user_id or not prompt_id:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': '*'
            },
            'body': json.dumps({'error': 'Missing required fields'})
        }

    response = table.get_item(
        Key={
            'user_id': user_id,
            'prompt_id': prompt_id
        }
    )
    if not response.get('Item'):
        return {
            'statusCode': 403,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': '*'
            },
            'body': json.dumps({'error': 'Prompt belongs to public, no permission to update'})
        }

    update_expression = 'SET '
    expression_attribute_values = {}
    update_attributes = []

    industry_type = body.get('industry_type', '').strip()
    if industry_type:
        update_attributes.append('industry_type = :industry_type')
        expression_attribute_values[':industry_type'] = industry_type

    system_prompt = body.get('system_prompt', '').strip()
    if system_prompt:
        update_attributes.append('system_prompt = :system_prompt')
        expression_attribute_values[':system_prompt'] = system_prompt

    user_prompt = body.get('user_prompt', '').strip()
    if user_prompt:
        update_attributes.append('user_prompt = :user_prompt')
        expression_attribute_values[':user_prompt'] = user_prompt

    topic_name = body.get('topic_name', '').strip()
    if topic_name:
        update_attributes.append('topic_name = :topic_name')
        expression_attribute_values[':topic_name'] = topic_name

    if not update_attributes:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': '*'
            },
            'body': json.dumps({'error': 'No fields to update'})
        }

    update_expression += ', '.join(update_attributes)

    try:
        table.update_item(
            Key={
                'user_id': user_id,
                'prompt_id': prompt_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': '*'
        },
        'body': json.dumps({'message': 'Prompt updated successfully'})
    }

def delete_prompt(body):
    user_id = body.get('user_id', '').strip()
    prompt_id = body.get('prompt_id', '').strip()

    response = table.get_item(
        Key={
            'user_id': user_id,
            'prompt_id': prompt_id
        }
    )

    if not response.get('Item'):
        return {
            'statusCode': 403,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': '*'
            },
            'body': json.dumps({'error': 'Prompt belongs to public, no permission to delete'})
        }

    topic_name = response['Item']['topic_name']

    table.delete_item(
        Key={
            'user_id': user_id,
            'prompt_id': prompt_id
        }
    )

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': '*'
        },
        'body': json.dumps({'message': f'Prompt {topic_name} has been deleted'})
    }
