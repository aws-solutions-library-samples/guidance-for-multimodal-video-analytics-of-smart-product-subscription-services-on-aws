import aws_cdk as core
import aws_cdk.assertions as assertions

from multimodal_analysis_cdk.multimodal_analysis_cdk_stack import MultimodalAnalysisCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in multimodal_analysis_cdk/multimodal_analysis_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = MultimodalAnalysisCdkStack(app, "multimodal-analysis-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
