import json
import boto3
import os

def lambda_handler(event, context):
    command = event['command']
    print(command)
    iot_data = boto3.client('iot-data')
    iot_message = {"message": command}
    topic = "camera/alarm" # You can get message from IoT Core MQTT test client with this topic
    response = iot_data.publish(
        topic=topic,
        qos=1,
        payload=json.dumps(iot_message)
        )
    HTTP_Status_Code = response['ResponseMetadata']['HTTPStatusCode']
    device_mqtt_response = {
        'statusCode': HTTP_Status_Code,
        'body': f'{topic}to device successfully triggered'
    }
    
    return json.dumps(device_mqtt_response)
