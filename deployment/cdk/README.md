# MultiModalVideoAnalystic-CDK Deployment
## Prerequisite

1. AWS credential is ready such as aws configure or environment, prefer administrator permission and us-east-1 region. reference https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html

2. AWS CDK v2 for python is ready, reference https://docs.aws.amazon.com/zh_cn/cdk/v2/guide/getting_started.html

3. Python boto3 is ready, reference https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#installation
4. Ensure bedrock Athropic Claude models permission. Model recommendation: Claude3.5 sonnet and Claude3 haiku for video analysis/postprocess. Be care that Claude3 sonnet is not appropriate for postprocess jobs
5. Optional function tools in postprocess may need other services preparation at advance, such as mail notification need sns topic ready
## CDK Content
This CDK code contains 4 stacks and deploys a multi-modal video analysis system, including S3 buckets, DynamoDB tables, Lambda functions, an API Gateway WebSocket API, Cognito authentication, and a frontend web application.

1. MultiModalVideoAnalyticsStorageStack:

    Creates 3 S3 Buckets:

    * web-app-bucket: used to deploy the frontend web application

    * video-upload-bucket: used to upload video files

    * video-information-bucket: used to store video analysis results  
    
    Creates Opensearch Domain:
    * Opensearch: used to retrieve frame  
    
    Creates 4 DynamoDB Tables:
    * DynamoDBPromptSample: used to store conversation prompts
    * DynamoDBConnectionID: used to store WebSocket connection IDs
    * DynamoDBChatHistory: used to store chat history
    * DynamoDBResult: used to store video analysis results
2. MultiModalVideoAnalyticsLambdaStack:

    Creates 3 Lambda Layers:
    * boto3: for the Python boto3 library
    * ffmpeg: for video processing
    * opensearch: for opensearch-client
    
    Creates 17 Lambda Functions:
    * websocket_notify: used to notify WebSocket clients
    * websocket_connect: used to handle WebSocket connections
    * websocket_disconnect: used to handle WebSocket disconnections
    * websocket_default: used to handle the default WebSocket route
    * get_kvs_streaming_url: used to get the Kinesis Video Streams stream URL
    * get_s3_presigned_url: used to get the S3 pre-signed URL
    * get_s3_video_url: used to get the S3 video file URL
    * list_s3_videos: used to list the video files in the S3 bucket
    * video_summary: used to generate video summaries
    * video_analysis: used to perform video analysis
    * frame_extraction: used to extract frames from videos
    * configure_video_resource: used to configure video resources
    * prompt_management_ws: used to manage conversation prompts
    * vqa_chatbot: used to handle the visual question-answering chatbot
    * agent_tool_send_device_mqtt: used to send device MQTT messages
    * agent_tool_send_notification: used to send notifications
    * opensearch_ingest: used to multi-modal embedding
    * opensearch_retrieve: used to frame retrieve from opensearch
3. MultiModalVideoAnalyticsAPIStack:

    Creates an API Gateway WebSocket API
    
    Adds the following WebSocket routes:
    * $connect: used to handle WebSocket connections
    * $disconnect: used to handle WebSocket disconnections
    * $default: used to handle the default WebSocket route
    * configure_agent: used to configure the agent
    * configure_video_resource: used to configure video resources
    * get_kvs_streaming_url: used to get the Kinesis Video Streams stream URL
    * get_s3_presigned_url: used to get the S3 pre-signed URL
    * get_s3_video_url: used to get the S3 video file URL
    * list_prompt: used to list the conversation prompts
    * list_s3_videos: used to list the video files in the S3 bucket
    * vqa_chatbot: used to handle the visual question-answering chatbot
    * opensearch_retrieve: used to frame retrieve from opensearch
4. MultiModalVideoAnalyticsWebAppStack:

    * Creates a Cognito user pool and     application client
    * Deploys the frontend web application to an S3 bucket
    * Creates a CloudFront distribution to serve the frontend web application
## Deployment use CDK
#### Get project repo
```
git clone git@ssh.gitlab.aws.dev:aws-gcr-solutions/industry-assets/mfg/guidance-for-multi-modal-video-analytics.git 
```
or [download](https://gitlab.aws.dev/aws-gcr-solutions/industry-assets/mfg/guidance-for-multi-modal-video-analytics/-/archive/CDK-Development/guidance-for-multi-modal-video-analytics-CDK-Development.tar.gz) repo to local.
#### Environment Setup
The solution uses Cloud9 for the build process.

Log in to the AWS console, go to the Cloud9 service, and select "Create environment".

![cdk-1](kvs_configuration_tutorial/pic/cdk-1.png)

Set the Cloud9 EC2 Name to "MultiModalVideoAnalysticDeploy", select the instance type as "t3.large", and choose the Platform as "Amazon Linux 2023". Keep the rest of the configuration as default, and click "Create". Wait for the creation to complete.

![cdk-2](kvs_configuration_tutorial/pic/cdk-2.png)

Click "Open" to enter the Cloud9 environment.

![cdk-3](kvs_configuration_tutorial/pic/cdk-3.png)

Upload the code if you download to local.Choose File-Upload Local Files... to upload
![cdk-4](kvs_configuration_tutorial/pic/cdk-4.png)
unzip the code using Cloud9 terminal
```
tar -xvf guidance-for-multi-modal-video-analytics-CDK-Development.tar.gz
```
![cdk-5](kvs_configuration_tutorial/pic/cdk-5.png)

cdk and boto3 environment build
```
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip
python3 -m pip install aws-cdk.aws-codestar-alpha
pip install boto3
pip install opensearch-py
```
#### Deployment
```
cd guidance-for-multi-modal-video-analytics-CDK-Development/cdk
cdk synth
cdk bootstrap
cdk deploy --all --require-approval never
```
the duration time is about 40 minutes.

After cdk deploy is over, you will get many output parameters in console, record webappcloudfront.

Additional configuration
```
python3 add_deployment.py
```
Follow the guidance, paste websocketapiid and promptdatabase
![cdk-6](kvs_configuration_tutorial/pic/cdk-6.png)
#### Usage
Go to login in the website
Enter the url webappcloudfront from browser, create an account, then you have completed the deployment

Video stream sample
If you want to test video stream as input resource, please check kvs_configuration_tutorial as a reference

#### Uninstall
If you want to uninstall the solution and release resources, please delete all the s3 content(bucket name started with multimodalvideoanalyticss) before uninstall.
```
cdk destroy --all
```