import aws_cdk as core
import aws_cdk.assertions as assertions

from urupraxis_secure_landing_zone.urupraxis_secure_landing_zone_stack import UrupraxisSecureLandingZoneStack

# example tests. To run these tests, uncomment this file along with the example
# resource in urupraxis_secure_landing_zone/urupraxis_secure_landing_zone_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = UrupraxisSecureLandingZoneStack(app, "urupraxis-secure-landing-zone")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
