#create a lambda function that can send message to aws IoT Core to certain devices
import boto3
from botocore.exceptions import ClientError

import json
import datetime

'''
Sample API Call:
{"body": str}

# Sample API Call Payload:
# {
# "body":{
#         "Device_ID: "device_id", #Optional, need only if send message to certain device
#         "Topic":"topic",
#         "Message":
#             {"msg":"message"}
#         }
# }

Sample Response:
{
"body":{
        "Topic":"topic",
        "Respose_Code":200,
        "Response_ID":"request_id"
        }
}
'''

def send_message(topic, message):
    client = boto3.client('iot-data')
    response = client.publish(
        topic=topic,
        qos=1,
        payload=json.dumps(message),
        contentType='UTF-8'
    )
    HTTP_Deaders = response['ResponseMetadata']['HTTPHeaders']
    HTTP_Status_Code = response['ResponseMetadata']['HTTPStatusCode']
    Request_ID = response['ResponseMetadata']['RequestId']
    Retry_Attempts = response['ResponseMetadata']['RetryAttempts']
    
    log_data = {
        "TimeStamp": str(datetime.datetime.now()),
        "HTTP_Deaders": HTTP_Deaders,
        "HTTP_Status_Code": HTTP_Status_Code,
        "Request_ID": Request_ID,
        "Retry_Attempts": Retry_Attempts
        }
    print(log_data)
    return response
  
def lambda_handler(event, context):
    # if 'Device_ID' not in event['body']:
    #     topic = event['body']['Topic']
    # else:
    #     topic = event['body']['Device_ID'] + '/' + event['Topic']
    
    # if 'Topic' not in event['body']:
    #     topic = 'alarm'
    # else:
    #     topic = event['body']['Topic']
    
    # for testing, using default topic 'alarm'
    topic = "kvs_camera_amlogic/alarm"
    message_raw = event["body"]
    message = {"msg":message_raw}
    response = send_message(topic, message)
    api_response = {
        "body":
            {
            "Topic": topic,
            "Respose_Code": response['ResponseMetadata']['HTTPStatusCode'],
            "Response_ID": response['ResponseMetadata']['RequestId']
            }
    }
    return api_response


