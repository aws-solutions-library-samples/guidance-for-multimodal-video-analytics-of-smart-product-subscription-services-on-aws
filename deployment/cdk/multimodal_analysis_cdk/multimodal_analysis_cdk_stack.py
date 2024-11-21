from aws_cdk import (
    Stack,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_logs as logs,
    aws_ecs_patterns as ecs_patterns,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_apigateway as apigw,
    aws_cognito as cognito,
    aws_opensearchservice as opensearch,
    aws_secretsmanager as secretmng,
    custom_resources as cr,
    aws_ec2,
    CfnParameter,
    RemovalPolicy,
    CfnOutput,
    Duration,
    Aws,
    Size,
    Environment,
    Tags
)
from constructs import Construct
import os
import json
from cdk_ecr_deployment import ECRDeployment, DockerImageName

class MultiModalVideoAnalyticsStorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket
        
        self.s3_bucket_web_app = s3.Bucket(
            self, 'web-app-bucket',
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            )
        
        self.s3_bucket_upload = s3.Bucket(
            self, "video-upload-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[s3.CorsRule(
                allowed_headers=["*"],
                allowed_methods=[s3.HttpMethods.PUT, s3.HttpMethods.POST, s3.HttpMethods.DELETE],
                allowed_origins=["*"],
                exposed_headers=["x-amz-server-side-encryption", "x-amz-request-id", "x-amz-id-2"],
                max_age=3000,
            )]
        )
        self.s3_bucket_information = s3.Bucket(
            self, "video-information-bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            )
        self.public_file = s3_deployment.BucketDeployment(
            self, 'public',
            sources=[s3_deployment.Source.asset('../../assets/resource')],
            destination_bucket=self.s3_bucket_upload
        )

        # DynamoDB Tables
        self.dynamo_prompt_sample = dynamodb.Table(
            self, "DynamoDBPromptSample",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="prompt_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.dynamo_connection_id = dynamodb.Table(
            self, "DynamoDBConnectionID",
            partition_key=dynamodb.Attribute(name="connectionId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.dynamo_chat_history = dynamodb.Table(
            self, "DynamoDBChatHistory",
            partition_key=dynamodb.Attribute(name="UserId", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SessionId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.dynamo_result = dynamodb.Table(
            self, "DynamoDBResult",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="sort_key", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Opensearch domain

        self.master_user_secret = secretmng.Secret(self, "OpenSearchMasterUserSecret",
          generate_secret_string=secretmng.SecretStringGenerator(
            secret_string_template=json.dumps({"username": "admin"}),
            generate_string_key="password",
            # Master password must be at least 8 characters long and contain at least one uppercase letter,
            # one lowercase letter, one number, and one special character.
            password_length=12
          ),
          secret_name = "opensearch-master-user"
        )

        #XXX: aws cdk elastsearch example - https://github.com/aws/aws-cdk/issues/2873
        self.ops_domain = opensearch.Domain(self, "OpenSearch",
          version=opensearch.EngineVersion.OPENSEARCH_2_13,
          capacity={
            "data_nodes": 1,
            "data_node_instance_type": "m5.large.search",
            "multi_az_with_standby_enabled":False
          },
          ebs={
            "volume_size": 20,
            "volume_type": aws_ec2.EbsDeviceVolumeType.GP3
          },
          fine_grained_access_control=opensearch.AdvancedSecurityOptions(
            master_user_name=self.master_user_secret.secret_value_from_json("username").unsafe_unwrap(),
            master_user_password=self.master_user_secret.secret_value_from_json("password")
          ),
          # Enforce HTTPS is required when fine-grained access control is enabled.
          enforce_https=True,
          # Node-to-node encryption is required when fine-grained access control is enabled
          node_to_node_encryption=True,
          # Encryption-at-rest is required when fine-grained access control is enabled.
          encryption_at_rest={
            "enabled": True
          },
          use_unsigned_basic_auth=True,   #default: False
          removal_policy=RemovalPolicy.DESTROY # default: RemovalPolicy.RETAIN
        )
        Tags.of(self.ops_domain).add('Name', 'multimodalsearch-ops')

        self.search_domain_endpoint = self.ops_domain.domain_endpoint


class MultiModalVideoAnalyticsLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, storage_stack: MultiModalVideoAnalyticsStorageStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda Layers
        self.layer_boto3 = lambda_.LayerVersion(
            self, "boto3",
            code=lambda_.Code.from_asset("../../assets/layer/boto3-python-layer.zip"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9]
        )
        self.layer_ffmpeg = lambda_.LayerVersion(
            self, "ffmpeg",
            code=lambda_.Code.from_asset("../../assets/layer/ffmpeg-python-layer.zip"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9]
        )
        self.layer_opensearch = lambda_.LayerVersion(
            self, "opensearchpy",
            code=lambda_.Code.from_asset("../../assets/layer/opensearch-python-layer.zip"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_9,lambda_.Runtime.PYTHON_3_11]
        )
        self.layer_rerank = lambda_.LayerVersion(
            self, "rerank",
            code=lambda_.Code.from_asset("../../assets/layer/rerank-python-layer.zip"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11]
        )

        # Lambda Role
        self.lambda_role_admin = iam.Role(
            self, "lambda-admin-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        self.lambda_role_admin.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess"))

        # Lambda Functions
        self.websocket_notify = lambda_.Function(
            self, "websocket_notify",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/websocket_notify"),
            handler="lambda_function.lambda_handler",
            role=self.lambda_role_admin,
            environment={
                "ENDPOINT_URL": "placeholder"
            }
        )

        self.websocket_connect = lambda_.Function(
            self, "websocket_connect",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/websocket_connect"),
            handler="lambda_function.lambda_handler",
            role=self.lambda_role_admin,
            environment={
                "TABLE_NAME": storage_stack.dynamo_connection_id.table_name
            }
        )
        self.websocket_connect.node.add_dependency(storage_stack.dynamo_connection_id)

        self.websocket_disconnect = lambda_.Function(
            self, "websocket_disconnect",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/websocket_disconnect"),
            handler="lambda_function.lambda_handler",
            role=self.lambda_role_admin,
            environment={
                "TABLE_NAME": storage_stack.dynamo_connection_id.table_name
            }
        )
        self.websocket_disconnect.node.add_dependency(storage_stack.dynamo_connection_id)

        self.websocket_default = lambda_.Function(
            self, "websocket_default",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/websocket_default"),
            handler="lambda_function.lambda_handler",
            role=self.lambda_role_admin,
        )

        self.get_kvs_streaming_url = lambda_.Function(
            self, "get_kvs_streaming_url",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/get_kvs_streaming_url"),
            handler="lambda_function.lambda_handler",
            role=self.lambda_role_admin,
        )

        self.get_s3_presigned_url = lambda_.Function(
            self, "get_s3_presigned_url",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/get_s3_presigned_url"),
            handler="lambda_function.lambda_handler",
            role=self.lambda_role_admin,
            environment={
                "UPLOAD_BUCKET": storage_stack.s3_bucket_upload.bucket_name,
            }
        )
        self.get_s3_presigned_url.node.add_dependency(storage_stack.s3_bucket_upload)

        self.get_s3_video_url = lambda_.Function(
            self, "get_s3_video_url",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/get_s3_video_url"),
            handler="lambda_function.lambda_handler",
            role=self.lambda_role_admin,
            environment={
                "VIDEO_BUCKET_NAME": storage_stack.s3_bucket_upload.bucket_name,
            }
        )

        self.list_s3_videos = lambda_.Function(
            self, "list_s3_videos",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/list_s3_videos"),
            handler="lambda_function.lambda_handler",
            role=self.lambda_role_admin,
            environment={
                "VIDEO_BUCKET_NAME": storage_stack.s3_bucket_upload.bucket_name,
            }
        )
        self.list_s3_videos.node.add_dependency(storage_stack.s3_bucket_upload)

        self.opensearch_ingest = lambda_.Function(
            self, "opensearch_ingest",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/opensearch_ingest"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(60),
            role=self.lambda_role_admin,
            layers=[self.layer_opensearch],
            environment={
                "OPENSEARCH_ENDPOINT": storage_stack.ops_domain.domain_endpoint,
                "INDEX_NAME": "multimodal-knn-index"
            }
        )
        self.opensearch_ingest.node.add_dependency(storage_stack.ops_domain, self.layer_opensearch)

        self.opensearch_retrieve = lambda_.Function(
            self, "opensearch_retrieve",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("../../source/lambda/opensearch_retrieve"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(60),
            role=self.lambda_role_admin,
            layers=[self.layer_opensearch, self.layer_rerank],
            memory_size=1024,
            ephemeral_storage_size=Size.mebibytes(1024),
            environment={
                "OPENSEARCH_ENDPOINT": storage_stack.ops_domain.domain_endpoint,
                "INDEX_NAME": "multimodal-knn-index",
                "RERANK":"N",
                "PREPROCESS":"N"
            }
        )
        self.opensearch_retrieve.node.add_dependency(storage_stack.ops_domain, self.layer_opensearch, self.layer_rerank)

        self.video_summary = lambda_.Function(
            self, "video_summary",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/video_summary"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(60),
            role=self.lambda_role_admin,
            layers=[self.layer_boto3],
            environment={
                "NotifyLambda": self.websocket_notify.function_name,
                "RESULT_DYNAMODB": storage_stack.dynamo_result.table_name
            }
        )
        self.video_summary.node.add_dependency(storage_stack.dynamo_result, self.websocket_notify, self.layer_boto3)

        self.video_analysis = lambda_.Function(
            self, "video_analysis",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/video_analysis"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(60),
            role=self.lambda_role_admin,
            layers=[self.layer_boto3],
            environment={
                "NOTIFY_LAMBDA": self.websocket_notify.function_name,
                "SUMMARY_LAMBDA": self.video_summary.function_name,
                "OPS_INGEST_LAMBDA": self.opensearch_ingest.function_name,
                "RESULT_BUCKET": storage_stack.s3_bucket_information.bucket_name,
                "RESULT_DYNAMODB": storage_stack.dynamo_result.table_name,
            }
        )
        self.video_analysis.node.add_dependency(
            storage_stack.dynamo_result, 
            self.websocket_notify, 
            self.video_summary, 
            self.opensearch_ingest,
            storage_stack.s3_bucket_information, 
            self.layer_boto3)

        self.frame_extraction = lambda_.Function(
            self, "frame_extraction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/frame_extraction"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(900),
            memory_size=1024,
            ephemeral_storage_size=Size.mebibytes(1024),
            role=self.lambda_role_admin,
            layers=[self.layer_ffmpeg],
            environment={
                "VIDEO_UPLOAD_BUCKET_NAME": storage_stack.s3_bucket_upload.bucket_name,
                "VIDEO_INFO_BUCKET_NAME": storage_stack.s3_bucket_information.bucket_name,
                "VIDEO_ANALYSIS_LAMBDA": self.video_analysis.function_name,
            }
        )
        self.frame_extraction.node.add_dependency(self.layer_ffmpeg, self.video_analysis, storage_stack.s3_bucket_upload, storage_stack.s3_bucket_information)

        self.configure_video_resource = lambda_.Function(
            self, "configure_video_resource",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/configure_video_resource"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(10),
            memory_size=128,
            role=self.lambda_role_admin,
            environment={
                "VIDEO_UPLOAD_BUCKET_NAME": storage_stack.s3_bucket_upload.bucket_name,
                "VIDEO_INFO_BUCKET_NAME": storage_stack.s3_bucket_information.bucket_name,
                "VIDEO_ANALYSIS_LAMBDA": self.video_analysis.function_name,
                "FRAME_EXTRACTION_LAMBDA": self.frame_extraction.function_name,
                "FRAME_EXTRACTION_PLATFORM": "lambda"
            }
        )
        self.configure_video_resource.node.add_dependency(self.frame_extraction, storage_stack.s3_bucket_information, storage_stack.s3_bucket_upload, storage_stack.s3_bucket_information)

        self.prompt_management_ws = lambda_.Function(
            self, "prompt_management",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/prompt_management_ws"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(10),
            role=self.lambda_role_admin,
            environment={
                "PUBLIC_USER": "public",
                "PROMPT_DYNAMODB": storage_stack.dynamo_prompt_sample.table_name
            }
        )

        self.vqa_chatbot = lambda_.Function(
            self, "vqa_chatbot",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/vqa_chatbot"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(60),
            memory_size=1024,
            role=self.lambda_role_admin,
            layers=[self.layer_boto3],
            environment={
                "HISTORY_DYNAMODB": storage_stack.dynamo_chat_history.table_name,
                "RESULT_DYNAMODB": storage_stack.dynamo_result.table_name
            }
        )
        self.vqa_chatbot.node.add_dependency(storage_stack.dynamo_chat_history, storage_stack.dynamo_result)

        self.agent_tool_send_device_mqtt = lambda_.Function(
            self, "agent_tool_send_device_mqtt",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/agent_tool_send_device_mqtt"),
            handler="lambda_function.lambda_handler",
            role=self.lambda_role_admin,
        )

        self.agent_tool_send_notification = lambda_.Function(
            self, "agent_tool_send_notification",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/agent_tool_send_notification"),
            handler="lambda_function.lambda_handler",
            role=self.lambda_role_admin,
            environment={
                "SNS_TOPIC_ARN": "placeholder",
            }
        )

        self.postprocess_agent = lambda_.Function(
            self, "postprocess_agent",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/postprocess_agent"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(60),
            memory_size=1024,
            role=self.lambda_role_admin,
            layers=[self.layer_boto3],
            environment={
                "RESULT_DYNAMODB": storage_stack.dynamo_result.table_name,
                "TOOL_DEVICE_LAMBDA": self.agent_tool_send_device_mqtt.function_name,
                "TOOL_NOTIFICATION_LAMBDA": self.agent_tool_send_notification.function_name
            }
        )
        self.postprocess_agent.node.add_dependency(storage_stack.dynamo_result, self.agent_tool_send_device_mqtt, self.agent_tool_send_notification)

        self.delete_resource = lambda_.Function(
            self, "delete_resource",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../../source/lambda/delete_resource"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(60),
            role=self.lambda_role_admin,
            layers=[self.layer_opensearch],
            environment={
                "RESULT_DYNAMODB": storage_stack.dynamo_result.table_name,
                "OPENSEARCH_ENDPOINT": storage_stack.ops_domain.domain_endpoint,
                "UPLOAD_BUCKET": storage_stack.s3_bucket_upload.bucket_name,
                "INDEX_NAME": "multimodal-knn-index"
            }
        )
        self.postprocess_agent.node.add_dependency(storage_stack.dynamo_result, storage_stack.ops_domain, storage_stack.s3_bucket_upload)

        self.prompt_list = lambda_.Function(
        self, "prompt_list",
        runtime=lambda_.Runtime.PYTHON_3_10,
        code=lambda_.Code.from_asset("../../source/lambda/prompt_list"),
        handler="prompt_list.lambda_handler",  # 只包含函数名称
        timeout=Duration.seconds(10),
        role=self.lambda_role_admin,
        environment={
            "PROMPT_DYNAMODB": storage_stack.dynamo_prompt_sample.table_name
        }
        )

        self.prompt_post_put_delete = lambda_.Function(
        self, "prompt_post_put_delete",
        runtime=lambda_.Runtime.PYTHON_3_10,
        code=lambda_.Code.from_asset("../../source/lambda/prompt_post_put_delete"),
        handler="prompt_post_put_delete.lambda_handler",  # 只包含函数名称
        timeout=Duration.seconds(10),
        role=self.lambda_role_admin,
        environment={
            "PROMPT_DYNAMODB": storage_stack.dynamo_prompt_sample.table_name
        }
    )
        
class MultiModalVideoAnalyticsECSStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # 1. Create docker repo
        repo = ecr.Repository(self, "FrameExtractionRepository",
                             repository_name="frame_extraction")

        # 2. use DockerImageAsset to create Docker image
        docker_image = ecr_assets.DockerImageAsset(self, "FrameExtractionImage",
                                                   directory="../modules/ecs/frame_extraction")

        # 3. Deploy Docker image to private ECR
        ecr_deployment = ECRDeployment(self, "DeployFrameExtractionImage",
                                       dest=DockerImageName(f"{Stack.of(self).account}.dkr.ecr.{Stack.of(self).region}.amazonaws.com/frame_extraction:latest"),
                                       src=DockerImageName(docker_image.image_uri)
                                      )

        # 4. Create an ECS Cluster
        cluster = ecs.Cluster(self, "FrameExtractionCluster",
                              cluster_name="frame_extraction_cluster")
        
        # 5. Create ECS Task Execution Role with necessary permissions
        task_execution_role = iam.Role(self, "EcsTaskExecutionRole",
                              assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
                              managed_policies=[
                                  iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                                  iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_FullAccess"),
                                  iam.ManagedPolicy.from_aws_managed_policy_name("AmazonKinesisVideoStreamsFullAccess")
                              ])
        
        # 6. Create ECS Task Definition
        task_definition = ecs.FargateTaskDefinition(self, "FrameExtractionTaskDefinition",
                                                    family="frame-extraction-task",
                                                    task_role=task_execution_role,
                                                    execution_role=task_execution_role,
                                                    memory_limit_mib=4096,
                                                    cpu=2048)
        
        # 7. Define the container within the task definition
        container = task_definition.add_container("frame_extraction",
                                                  image=ecs.ContainerImage.from_ecr_repository(repo, "latest"),
                                                  logging=ecs.LogDriver.aws_logs(
                                                      stream_prefix="ecs",
                                                      log_group=logs.LogGroup(self, "FrameExtractionLogGroup",
                                                                              log_group_name="/ecs/frame-extraction-task",
                                                                              removal_policy=RemovalPolicy.DESTROY)
                                                  ))
        
        # 8. Define port mapping
        container.add_port_mappings(ecs.PortMapping(container_port=80, host_port=80, protocol=ecs.Protocol.TCP))

class MultiModalVideoAnalyticsAPIStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, lambda_stack: MultiModalVideoAnalyticsLambdaStack, storage_stack: MultiModalVideoAnalyticsStorageStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.websocket_api = apigwv2.WebSocketApi(self, "multimodal_analysis_api", route_selection_expression="$request.body.action")
        self.websocket_api.node.add_dependency(
            lambda_stack.websocket_notify, lambda_stack.websocket_connect, lambda_stack.websocket_disconnect,
            lambda_stack.websocket_default, lambda_stack.postprocess_agent, lambda_stack.configure_video_resource,
            lambda_stack.get_kvs_streaming_url, lambda_stack.get_s3_presigned_url, lambda_stack.prompt_management_ws,
            lambda_stack.list_s3_videos, lambda_stack.vqa_chatbot
        )

        # Add routes
        self.ws_connect = self.websocket_api.add_route(
            "$connect",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("ConnectIntegration", lambda_stack.websocket_connect)
        )
        self.ws_disconnect = self.websocket_api.add_route(
            "$disconnect",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("DisconnectIntegration", lambda_stack.websocket_disconnect)
        )
        self.ws_default = self.websocket_api.add_route(
            "$default",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("DefaultIntegration", lambda_stack.websocket_default)
        )
        self.ws_postprocess = self.websocket_api.add_route(
            "configure_agent",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("ConfigureAgent", lambda_stack.postprocess_agent),
            return_response=True
        )
        self.ws_cfg = self.websocket_api.add_route(
            "configure_video_resource",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("ConfigureVideoResource", lambda_stack.configure_video_resource),
            return_response=True
        )
        self.ws_kvs = self.websocket_api.add_route(
            "get_kvs_streaming_url",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("GetKVSStreamingUrl", lambda_stack.get_kvs_streaming_url),
            return_response=True
        )
        self.ws_presignurl = self.websocket_api.add_route(
            "get_s3_presigned_url",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("GetS3PresignedUrl", lambda_stack.get_s3_presigned_url),
            return_response=True
        )
        self.ws_videourl = self.websocket_api.add_route(
            "get_s3_video_url",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("GetS3VideoUrl", lambda_stack.get_s3_video_url),
            return_response=True
        )
        self.ws_prompt = self.websocket_api.add_route(
            "list_prompt",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("ListPrompt", lambda_stack.prompt_management_ws),
            return_response=True
        )
        self.ws_videos = self.websocket_api.add_route(
            "list_s3_videos",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("ListS3Videos", lambda_stack.list_s3_videos),
            return_response=True
        )
        self.ws_chatbot = self.websocket_api.add_route(
            "vqa_chatbot",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("VQAChatbot", lambda_stack.vqa_chatbot),
            return_response=True
        )
        self.ws_retrieve = self.websocket_api.add_route(
            "opensearch_retrieve",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("OPSRetrieve", lambda_stack.opensearch_retrieve),
            return_response=True
        )
        self.delete_resource = self.websocket_api.add_route(
            "delete_resource",
            integration=apigwv2_integrations.WebSocketLambdaIntegration("DeleteResource", lambda_stack.delete_resource),
            return_response=True
        )
        self.dev_stage = apigwv2.WebSocketStage(
            self, "ProductionStage",
            web_socket_api=self.websocket_api,
            stage_name="production",
            auto_deploy=True
        )
        self.dev_stage.node.add_dependency(
            self.ws_connect, self.ws_disconnect, self.ws_default, self.ws_postprocess, self.ws_cfg, self.ws_kvs, self.ws_presignurl, self.ws_videourl, self.ws_prompt, self.ws_videos, self.ws_chatbot
        )

        # Update Lambda environment variable
        region = Stack.of(self).region
        self.update_env_vars = cr.AwsCustomResource(
            self, "UpdateEnvVars",
            on_update=cr.AwsSdkCall(
                service="Lambda",
                action="updateFunctionConfiguration",
                parameters={
                    "FunctionName": lambda_stack.websocket_notify.function_name,
                    "Environment": {
                        "Variables": {
                            "ENDPOINT_URL": f"https://{self.websocket_api.api_id}.execute-api.{region}.amazonaws.com/{self.dev_stage.stage_name}"
                        }
                    },
                },
                physical_resource_id=cr.PhysicalResourceId.of(f"{lambda_stack.websocket_notify.function_name}-env-vars"),
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE),
        )
        self.update_env_vars.node.add_dependency(lambda_stack.websocket_notify, self.websocket_api, self.dev_stage)

        # Create the PromptEditApi
        self.prompt_edit_api = apigw.RestApi(
            self,
            "PromptEditApi",
            rest_api_name="PromptEditAPI",
            description="This is a REST API for handling prompt contents.",
            deploy_options=apigw.StageOptions(stage_name="Prod")
        )
        empty_model = apigw.Model.EMPTY_MODEL

        # Add /prompt_list GET
        prompt_lists_resource = self.prompt_edit_api.root.add_resource("prompt-list")
        # Add GET method integration
        prompt_lists_integration = apigw.LambdaIntegration(
            handler=lambda_stack.prompt_list
        )
        
        # Add OPTIONS method for /prompt_list
        prompt_lists_resource.add_method(
            "OPTIONS",
            apigw.MockIntegration(
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Headers": "'*'",
                            "method.response.header.Access-Control-Allow-Origin": "'*'",
                            "method.response.header.Access-Control-Allow-Methods": "'GET, OPTIONS'",
                        },
                    )
                ],
                request_templates={
                    "application/json": '{"statusCode": 200}'
                },
            ),
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                )
            ],
        )
        prompt_lists_resource.add_method(
            "GET",
            prompt_lists_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                    response_models={
                        "application/json": empty_model
                    }
                ),
            ],
        )
        
        # Add /prompt_post_put_delete resource
        prompt_post_put_delete_resource = self.prompt_edit_api.root.add_resource("prompt")
        # Add OPTIONS method for /prompt_post_put_delete
        prompt_post_put_delete_resource.add_method(
            "OPTIONS",
            apigw.MockIntegration(
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code="200",
                        response_parameters={
                            "method.response.header.Access-Control-Allow-Headers": "'*'",
                            "method.response.header.Access-Control-Allow-Origin": "'*'",
                            "method.response.header.Access-Control-Allow-Methods": "'PUT,POST,DELETE,OPTIONS'",
                        },
                    )
                ],
                request_templates={
                    "application/json": '{"statusCode": 200}'
                },
            ),
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Headers": True,
                        "method.response.header.Access-Control-Allow-Methods": True,
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                )
            ],
        )
        
        # Add PUT method integration
        prompt_post_put_delete_put_integration = apigw.LambdaIntegration(
            handler=lambda_stack.prompt_post_put_delete
        )
        prompt_post_put_delete_resource.add_method(
            "PUT",
            prompt_post_put_delete_put_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                    response_models={
                        "application/json": empty_model
                    }
                ),
            ],
        )
        
        # Add POST method integration
        prompt_post_put_delete_post_integration = apigw.LambdaIntegration(
            handler=lambda_stack.prompt_post_put_delete
        )
        prompt_post_put_delete_resource.add_method(
            "POST",
            prompt_post_put_delete_post_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                    response_models={
                        "application/json": empty_model
                    }
                ),
            ],
        )
        
        # Add DELETE method integration
        prompt_post_put_delete_delete_integration = apigw.LambdaIntegration(
            handler=lambda_stack.prompt_post_put_delete
        )
        prompt_post_put_delete_resource.add_method(
            "DELETE",
            prompt_post_put_delete_delete_integration,
            method_responses=[
                apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Access-Control-Allow-Origin": True,
                    },
                    response_models={
                        "application/json": empty_model
                    }
                ),
            ],
        )
        

        ## Enable CORS for the API resources
        # prompt_lists_resource.add_cors_preflight(
        #     allow_origins=["*"],
        #     allow_methods=["GET", "OPTIONS"],
        #     allow_headers=["*"]
        # )
        # prompt_post_put_delete_resource.add_cors_preflight(
        #     allow_origins=["*"],
        #     allow_methods=["POST", "PUT", "DELETE", "OPTIONS"],
        #     allow_headers=["*"]
        # )




class MultiModalVideoAnalyticsWebAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, storage_stack: MultiModalVideoAnalyticsStorageStack, api_stack: MultiModalVideoAnalyticsAPIStack, lambda_stack: MultiModalVideoAnalyticsLambdaStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Cognito configuration
        self.user_pool = cognito.UserPool(
            self, "UserPool",
            sign_in_aliases={"username": True, "email": True},
            auto_verify={"email": True},
            self_sign_up_enabled=True,
            keep_original={"email": True},
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.app_client = self.user_pool.add_client(
            "sample-app-client",
            user_pool_client_name="sample-app-client",
            auth_flows=cognito.AuthFlow(user_srp=True)
        )

        # S3 configuration
        self.s3_bucket_web_app = storage_stack.s3_bucket_web_app
        self.s3_bucket_upload = storage_stack.s3_bucket_upload
        self.s3_bucket_information = storage_stack.s3_bucket_information

        # WebSocket configuration
        self.websocket_api = api_stack.websocket_api
        self.dev_stage = api_stack.dev_stage

        # Front End Content
        self.web_app_file = s3_deployment.BucketDeployment(
            self, 'web-app-bucket-deployment',
            sources=[s3_deployment.Source.asset('../../web-app/dist')],
            destination_bucket=self.s3_bucket_web_app
        )

        self.assets_dir = os.path.join('../..', 'web-app', 'dist', 'assets')
        self.js_file_path = next(os.path.join(self.assets_dir, file_name) for file_name in os.listdir(self.assets_dir) if
                            file_name.startswith('envConfig-'))
        self.js_file_name = os.path.basename(self.js_file_path)

        with open(self.js_file_path, 'r') as file:
            self.content = file.read()

        if self.content:
            # Cognito configuration
            self.content = self.content.replace('vite.cognito.region', self.region)
            self.content = self.content.replace('vite.cognito.user.pool.id', self.user_pool.user_pool_id)
            self.content = self.content.replace('vite.cognito.user.pool.web.client.id', self.app_client.user_pool_client_id)

            # S3 configuration
            self.content = self.content.replace('vite.storage.video.bucket', self.s3_bucket_upload.bucket_name)
            self.content = self.content.replace('vite.storage.information.bucket', self.s3_bucket_information.bucket_name)

            # Websocket configuration
            self.content = self.content.replace('vite.websocket.url', f'{self.websocket_api.api_endpoint}/{self.dev_stage.stage_name}')

            # Restful API configuration
            self.content = self.content.replace('vite.http.url', f'https://{api_stack.prompt_edit_api.rest_api_id}.execute-api.{self.region}.amazonaws.com/{api_stack.prompt_edit_api.deployment_stage.stage_name}')


            self.put_s3_statement = iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['s3:GetObject', 's3:PutObject', 's3:DeleteObject'],
                resources=[f'{self.s3_bucket_web_app.bucket_arn}/*']
            )

            self.js_file_id = "web-app-js-file"
            self.web_app_config = cr.AwsCustomResource(
                self, self.js_file_id,
                on_update=cr.AwsSdkCall(
                    service='S3',
                    action='putObject',
                    parameters={
                        'Bucket': self.s3_bucket_web_app.bucket_name,
                        'Key': f'assets/{self.js_file_name}',
                        'Body': self.content,
                        'ContentType': 'application/javascript'
                    },
                    physical_resource_id=cr.PhysicalResourceId.of(self.js_file_id)
                ),
                policy=cr.AwsCustomResourcePolicy.from_statements(
                    [self.put_s3_statement]
                )
            )
            self.web_app_config.node.add_dependency(self.web_app_file)

        self.web_app_distribution = cloudfront.Distribution(
            self, 'web-app-distribution',
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.s3_bucket_web_app),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY
            ),
            default_root_object='index.html',
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(10)
                ),
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(10)
                )
            ]
        )
        self.web_app_distribution.node.add_dependency(self.web_app_file)

        CfnOutput(self, 'web-app-cloudfront',value=self.web_app_distribution.distribution_domain_name, export_name='web-app-cloudfront')
        CfnOutput(self, "prompt-database", value=storage_stack.dynamo_prompt_sample.table_name, export_name="prompt-database")
        CfnOutput(self, "opsdomain", value=storage_stack.search_domain_endpoint, export_name="opsdomain")
        CfnOutput(self, 'opsdashboards', value=f"{storage_stack.search_domain_endpoint}/_dashboards/", export_name='opsdashboards')
        CfnOutput(self, 'mail-lambda', value=lambda_stack.agent_tool_send_notification.function_name, export_name='mail-lambda')
        CfnOutput(self, 'CRUBAPI', value=f'https://{api_stack.prompt_edit_api.rest_api_id}.execute-api.{self.region}.amazonaws.com/{api_stack.prompt_edit_api.deployment_stage.stage_name}', export_name='CRUBAPI')
        CfnOutput(self, "websocket-api-id", value=api_stack.websocket_api.api_id, export_name="websocket-api-id")

