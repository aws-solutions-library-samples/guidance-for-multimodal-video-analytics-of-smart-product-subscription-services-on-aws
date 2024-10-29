import boto3
import logging
import os
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import xml.etree.ElementTree as ET

dynamodb = boto3.resource('dynamodb')

query_table_name = os.environ["RESULT_DYNAMODB"]
query_table = dynamodb.Table(query_table_name)

def query_dynamodb(user_id, task_id):
    """
    查询 DynamoDB 表，获取指定用户和任务的数据
    
    Args:
        user_id (str): 用户 ID
        task_id (str): 任务 ID
        
    Returns:
        list: 查询结果列表
    """
    response = query_table.query(
        ProjectionExpression="video_time, frame_result",
        KeyConditionExpression=Key('user_id').eq(user_id) & Key('sort_key').begins_with(task_id)
    )
    return response['Items']

def create_xml(data):
    """
    根据查询结果创建 XML 文件
    
    Args:
        data (list): 查询结果列表
        user_id (str): 用户 ID
        task_id (str): 任务 ID
    """
    root = ET.Element('video_result')
    
    for item in data:
        result_item = ET.SubElement(root, 'item')
        timestamp = ET.SubElement(result_item, 'timestamp')
        timestamp.text = str(item['video_time'])
        frame_result = ET.SubElement(result_item, 'video_result')
        frame_result.text = item['frame_result']
    
    query_result = ET.tostring(root, encoding='utf-8').decode('utf-8')
    return query_result

