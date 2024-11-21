# Guidance for Multi-Modal Video Analytics of Smart Product Value-added Subscription Services on AWS


## Table of Content

List the top-level sections of the README template, along with a hyperlink to the specific section.

### Required

1. [Overview](#overview-required)
    - [Cost](#cost)
2. [Prerequisites](#prerequisites-required)
    - [Operating System](#operating-system-required)
3. [Deployment Steps](#deployment-steps-required)
4. [Deployment Validation](#deployment-validation-required)
5. [Running the Guidance](#running-the-guidance-required)
6. [Next Steps](#next-steps-required)
7. [Cleanup](#cleanup-required)

***Optional***

8. [FAQ, known issues, additional considerations, and limitations](#faq-known-issues-additional-considerations-and-limitations-optional)

## Overview

### **Background**  
The rapid advancement of AI technology has revolutionized video analysis, especially in smart cameras, devices and smart homes industry, moving away from traditional models that depend on extensive datasets and manual feature extraction. These older methods suffer from limited generalization, inability to handle multimodal data, and poor contextual understanding. In contrast, large multimodal models like Claude 3 overcome these limitations with automatic feature learning, strong generalization across diverse data, integrated processing of visual, audio, and text information, and robust contextual modeling. This allows for rapid validation and reduced development costs in specific business scenarios, bypassing the cumbersome steps of traditional models.
### - **What problem does this Guidance solve?** 
#### Video Analysis

When providing end users with basic camera functions while offering advanced video analysis, scene understanding, and event judgment capabilities. Traditionally, video analysis relied on computer vision algorithms and machine learning models that required training datasets or handcrafted feature extractors and classifiers. However, this approach had inherent limitations:

1. Dependence on training data. Traditional machine learning models needed substantial data to learn specific classifications or object locations, making the curation of sufficient training datasets time-intensive, and in some cases, difficult to obtain.
2. Laborious feature engineering requiring domain expertise. These models necessitated manually designing and extracting video features like color, texture, and shape - a complex and time-consuming process demanding extensive domain knowledge.
3. Limited generalization. Traditional models could typically only handle specific video data types, with performance degrading significantly when encountering new scenarios or data distributions.
4. Lack of contextual understanding. These models could not effectively capture contextual cues like object relationships and action semantics, which are crucial for accurate video comprehension.

#### Messages Push

After video analysis, it is often necessary to make judgments based on the results. When user-defined conditions are met, various types of notification messages need to be pushed. For instance, an end-user may request: "Send a text message to my phone when a fox is detected in my yard," or "Immediately notify the home alarm system if an intruder breaks into my house."
In such scenarios, intelligent camera manufacturers face the following challenges:

1. Evaluating video analysis results for real-time or scheduled alert triggering.
2. Accommodating personalized alert conditions for each end-user, making it difficult to meet diverse needs.
3. Implementing various post-alert message processing workflows, requiring significant research and development resources.

#### Visual Summary and Question&Answer

After analyzing and storing video data, the end user expects to retrieve, query, ask questions, and summarize specific events of interest efficiently. For instance, when continuously monitoring pets at home with video surveillance, the user should be able to quickly find relevant video clips through retrospective queries, replay, view, and summarize interesting details during a specific time period. However, traditional methods lack this capability.

#### Image Search
The video data and frames are stored in a vector database, enabling users to quickly locate specific images and corresponding video clips through natural language queries. For example, users can search by entering phrases like "My dog and I playing on the grass."


### - **Architecture Diagram**
![System Architecture Diagram](assets/images/diagram.png)  


1. The user ingests data, edits prompt, performs analytics and sets postprocessing actions on website which is hosted on AWS Amplify.
2. The website passes the request to Amazon API Gateway as well as receives the response from API Gateway.
3. API Gateway directs a request to the video streaming and upload component, which integrates video data from a Smart Camera via Amazon Kinesis Video Streams or AWS IoT Core. AWS IoT Greengrass. AWS IoT Greengrass is used to manage and deploy machine learning models to edge devices.
4. API Gateway forwards the analysis request, which includes video frames and prompt, to the visual analytics component. This component, equipped with an AWS Lambda function and model library, processes the request and returns the result from the language model to API Gateway.
5. If the user set a postprocess action via input natural language, LLM Agent will perform it through serval AWS Lambda functions such as sending SMS to mobile client or notifications to edge devices.
6. The user can store the videos on Amazon Simple Storage Service (Amazon S3) and fine-tune prompts on Amazon DynamoDB.
7. The user have the option to save intermediate results of video analysis to Amazon OpenSearch through AWS Lambda function. Then, on the website, they can utilize LLM to conduct question-and-answer sessions based on the video content.

### Cost

### Sample Cost Table

The following table provides a sample cost breakdown for deploying this Guidance with the default parameters in the US East (N. Virginia) Region for one month(On-Demand).

| AWS service  | Dimensions [Token Number] | Input Token Cost [USD] |Output Token Cost [USD] |
| ----------- | ------------ | ------------ |------------ |
| Amazon Bedrock Claude3 Haiku | 1 Million  | $ 0.25 |$ 1.25 |
| Amazon Bedrock Claude3.5 Sonnet-v2 | 1 Millon | $ 3.00 |$ 15.00 |

| AWS service  | Spacification | Pricing|
| ----------- | ------------ | ------------ |
| Amazon OpenSearch Service | 	1 domain  m5.large.search, per month | $ 103.66 |
| Amazon DynamoDB |  100000 write, 1000 read , per month| $ 2.6 |

## Prerequisites 

### AWS account requirements
**resources:**
- Bedrock and Claude3 model access
- S3 bucket
- API Gateway 80/443 port access
- OpenSearch
- Lambda


### aws cdk bootstrap

This Guidance uses aws-cdk. If you are using aws-cdk for first time, please perform the below bootstrapping in your deployment ec2
```
$ sudo cdk bootstrap
```

### Supported Regions

- us-east-1
- us-west-2


## Deployment Steps
Your deployment ec2 should have pe

1. Clone the repo  
```bash
$ git clone https://github.com/aws-solutions-library-samples/guidance-for-multi-modal-video-analytics-of-smart-product-value-added-subscription-services-on-aws.git
```
2. cd to the repo folder   
```bash
$ cd guidance-for-multi-modal-video-analytics-main/deployment/cdk/
```
3. Install packages
```bash
sudo yum install python3-pip -y && \
sudo curl -sL https://rpm.nodesource.com/setup_18.x | sudo bash - && \
sudo yum install -y nodejs && \
sudo pip install aws-cdk.core && \
sudo pip install aws-cdk-lib constructs && \
sudo pip install --upgrade constructs && \
sudo pip install cdk-ecr-deployment && \
sudo python3 -m pip install --upgrade aws-cdk-lib && \
sudo npm install -g aws-cdk && \
pip install opensearch-py && \
sudo pip install boto3 && \
sudo yum install -y docker && \
sudo systemctl start docker
```
4. Run this command to deploy the stack 
```bash
$ sudo cdk deploy --all --require-approval never
``` 
5. After cdk deploy is over, you will get many output parameters in console, record webappcloudfront.



## Deployment Validation

* Open CloudFormation console and verify the status of the template, find a address like xxxxxxxxx.cloudfront.net.



## Running the Guidance

Go to login in the website
Enter the url webappcloudfront from browser, create an account, then you have completed the deployment
Video stream sample
If you want to test video stream as input resource, please check kvs_configuration_tutorial as a reference  


## Cleanup
```bash
$ sudo cdk destroy --all
```


## FAQ

* Question 1:  Can this guidance accept/process image input?   
Answer: No, this guidance currently only processes videos from S3 and video streams from KVS.

* Question 2: Can I perform video analysis through the API?  
Answer: Yes, you can use api Gateway URL to invoke.
