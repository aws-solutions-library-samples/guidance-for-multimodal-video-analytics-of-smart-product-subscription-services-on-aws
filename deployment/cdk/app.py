import aws_cdk as cdk
import sys

from multimodal_analysis_cdk.multimodal_analysis_cdk_stack import (
    MultiModalVideoAnalyticsStorageStack,
    MultiModalVideoAnalyticsLambdaStack,
    MultiModalVideoAnalyticsECSStack,
    MultiModalVideoAnalyticsWebAppStack,
    MultiModalVideoAnalyticsAPIStack
)

app = cdk.App()

create_ecs_stack = app.node.try_get_context('create_ecs_stack')

storage_stack = MultiModalVideoAnalyticsStorageStack(app, "MultiModalVideoAnalyticsStorageStack")
lambda_stack = MultiModalVideoAnalyticsLambdaStack(app, "MultiModalVideoAnalyticsLambdaStack", storage_stack=storage_stack)

if create_ecs_stack:
    ecs_stack = MultiModalVideoAnalyticsECSStack(app, "MultiModalVideoAnalyticsECSStack")

api_stack = MultiModalVideoAnalyticsAPIStack(app, "MultiModalVideoAnalyticsAPIStack", lambda_stack=lambda_stack, storage_stack=storage_stack)
web_app_stack = MultiModalVideoAnalyticsWebAppStack(app, "MultiModalVideoAnalyticsWebAppStack", storage_stack=storage_stack, api_stack=api_stack, lambda_stack=lambda_stack)

app.synth()