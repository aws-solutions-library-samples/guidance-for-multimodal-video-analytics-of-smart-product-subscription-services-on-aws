import json
import boto3
import os

def lambda_handler(event, context):
    condition = event['condition']
    message = event['message']
    receiver = event['receiver']
    print(condition, message, receiver)
    topic_arn = os.environ['SNS_TOPIC_ARN']
    sns = boto3.client('sns')

    response = sns.publish(
        TopicArn=topic_arn,
        Message=f'because of {condition}, you receive the mail about {message}',
        Subject= 'This is a notification from video analysis platform'
        )
    
    HTTP_Status_Code = response['ResponseMetadata']['HTTPStatusCode']
    notification_response = {
        'statusCode': HTTP_Status_Code,
        'body': 'SNS mail successfully triggered'
    }
    
    return json.dumps(notification_response)