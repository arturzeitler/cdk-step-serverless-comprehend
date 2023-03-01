import os

import aws_cdk

from stacks.serverless import GateWayStepFunction
from stacks.pipeline import CodePipeline

app = aws_cdk.App()
CodePipeline(app, "GateWayStepFunction", env=aws_cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')))
GateWayStepFunction(app, "GateWayStepFunction", env=aws_cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')))
app.synth()
