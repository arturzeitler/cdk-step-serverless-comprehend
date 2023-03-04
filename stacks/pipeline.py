from aws_cdk import (
    Stack,
    aws_codebuild,
    aws_codepipeline,
    aws_codepipeline_actions,
    SecretValue,
    aws_iam,
)

from constructs import Construct


class CodePipeline(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        """
        Building assets failed: Error: Building Assets Failed: Error: GateWayStepFunction: 
        User: arn:aws:sts::834458757077:assumed-role/CodePipeline-CDKCodeBuildRole4884F95D-AXNNMP5FM8KY/AWSCodeBuild-a37471a5-d047-457a-9fca-8ab67ac6afea is 
        not authorized to perform: ssm:GetParameter on resource: arn:aws:ssm:eu-central-1:834458757077:parameter/cdk-bootstrap/hnb659fds/version because no 
        identity-based policy allows the ssm:GetParameter action
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
                    owner="arturzeitler",
                    repo="cdk-step-serverless-comprehend",
                    branch="master",
                    action_name="CDK_Pipeline_Source",
                    oauth_token=SecretValue.secrets_manager("github-token"),
                    output=source_output,
                )
            ]
        )

        codebuild_role = aws_iam.Role(
            self,
            "CDKCodeBuildRole",
            assumed_by=aws_iam.ServicePrincipal("codebuild.amazonaws.com")
        )
        cf_policy = aws_iam.ManagedPolicy.from_managed_policy_arn(
            self,
            "CloudFormationRead",
            "arn:aws:iam::aws:policy/AWSCloudFormationReadOnlyAccess"
        )
        ssm_policy = aws_iam.ManagedPolicy.from_managed_policy_arn(
            self,
            "SSMGetParameter",
            "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess"
        )
        codebuild_role.add_managed_policy(
            cf_policy
        )
        codebuild_role.add_managed_policy(
            ssm_policy
        )
        codebuild_role.attach_inline_policy(
            aws_iam.Policy(self, "AssumeRole",
                           statements=[aws_iam.PolicyStatement(
                               actions=[
                                   "sts:AssumeRole",
                                   "iam:PassRole"
                               ],
                               resources=["arn:aws:iam::*:role/cdk*"],
                               effect=aws_iam.Effect.ALLOW
                           )]
                           )
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
                        ),
                        role=codebuild_role
                    )
                )
            ]
        )
