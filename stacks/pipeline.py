from aws_cdk import (
    Stack,
    aws_codebuild,
    aws_codepipeline,
    aws_codepipeline_actions,
    SecretValue,
)

from constructs import Construct


class CodePipeline(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        """
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
        """
        pipeline = aws_codepipeline.Pipeline(
            self,
            "CodePipeline-Pipeline",
            pipeline_name="Serverless-Pipeline",
            cross_account_keys=False,
            restart_execution_on_update=True
        )

        source_output = aws_codepipeline.Artifact("CDKSourceOutput")
        build_output = aws_codepipeline.Artifact("CDKBuildOutput")

        pipeline.add_stage(
            stage_name="Source",
            actions=[
                aws_codepipeline_actions.GitHubSourceAction(
                    owner="ArturZ.",
                    repo="cdk-step-serverless-comprehend",
                    branch="master",
                    action_name="CDK_Pipeline_Source",
                    oauth_token=SecretValue.secrets_manager("github-token"),
                    output=source_output,
                )
            ]
        )
        pipeline.add_stage(
            stage_name="Build",
            actions=[
                aws_codepipeline_actions.CodeBuildAction(
                    action_name="CDK_Pipeline_Build",
                    input=source_output,
                    outputs=[
                        build_output
                    ],
                    project=aws_codebuild.PipelineProject(
                        self,
                        "CodeBuild-Pipeline",
                        environment=aws_codebuild.BuildEnvironment(
                            build_image=aws_codebuild.LinuxBuildImage.AMAZON_LINUX_2_4
                        ),
                        build_spec=aws_codebuild.BuildSpec.from_source_filename(
                            "buildspec.yml"
                        )
                    )
                )
            ]
        )
