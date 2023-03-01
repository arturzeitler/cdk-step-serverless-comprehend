from aws_cdk import (
    Stack,
    aws_codebuild,
    aws_codepipeline,
)

from constructs import Construct


class CodePipeline(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pipeline = CodePipeline(self, "Pipeline",
                                pipeline_name="MyPipeline",
                                synth=aws_codepipeline.ShellStep("Synth",
                                                                 input=aws_codepipeline.CodePipelineSource.git_hub(
                                                                     "https://github.com/arturzeitler/cdk-step-serverless-comprehend", "master"),
                                                                 commands=["npm install -g aws-cdk",
                                                                           "python -m pip install -r requirements.txt",
                                                                           "cdk synth"]
                                                                 )
                                )
