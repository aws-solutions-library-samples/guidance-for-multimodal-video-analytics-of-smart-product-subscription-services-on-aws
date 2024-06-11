#create a lambda function that send mails using aws sns

'''
Sample API Call:
{"body":"xxxx->str"}

# Sample API Call Payload:
# {
#     "Send_Email": true|false,
#     "Send_SMS": true|false,
#     "TopicArn": "topic_arn",
#     "Message": "message"
# }

Sample Response:
{  
    "Topic":"topic",
    "Respose_Code":200,
    "Response_ID":"request_id"
}
'''

import boto3
import datetime

def lambda_handler(event, context):
    #print(event)
    #topic_arn = event['TopicArn']
    #for testing purpose, fixing the arn in the code
    topic_arn = "arn:aws:sns:us-east-1:058264304798:Multi-Modal_Send_Notification"
    message = event['body']
    #print(topic_arn)
    #print(message)
    client = boto3.client('sns')
    response = client.publish(
        TopicArn=topic_arn,
        Message=message,
        Subject='This is a test email send  to you address!'
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
    return {"body":
                {
                "Respose_Code": HTTP_Status_Code,
                'body': 'SNS API Call Successfully Triggered'
                }
    }