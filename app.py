import os
import json

from aws_cdk import (
    Stack,
    Duration,
    aws_lambda,
    aws_dynamodb,
    aws_iam,
    aws_apigateway,
    aws_stepfunctions,
    aws_stepfunctions_tasks,
    CfnOutput,
)
import aws_cdk
from constructs import Construct


class GateWayStepFunction(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table_name = 'Sentiment'

        dynamo_table = aws_dynamodb.Table(self, "DynamoDbTable",
                                          table_name=table_name,
                                          removal_policy=aws_cdk.RemovalPolicy.DESTROY,
                                          partition_key=aws_dynamodb.Attribute(name="id",
                                                                               type=aws_dynamodb.AttributeType.STRING),
                                          time_to_live_attribute="ttl",
                                          billing_mode=aws_dynamodb.BillingMode.PROVISIONED,
                                          read_capacity=2,
                                          write_capacity=2,
                                          )

        comprehend_policy = aws_iam.PolicyStatement(
            actions=[
                "comprehend:DetectDominantLanguage",
                "comprehend:DetectSentiment",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            resources=["*"],
            effect=aws_iam.Effect.ALLOW,
        )

        comprehend_lambda_fn = aws_lambda.Function(self, 'ComprehendLambdaFn',
                                                   runtime=aws_lambda.Runtime.PYTHON_3_9,
                                                   function_name="ComprehendLambdaRestApi",
                                                   handler="comprehend-handler.lambda_handler",
                                                   description='Function that returns Sentiment from AWS Comprehend',
                                                   code=aws_lambda.Code.from_asset(os.path.join(
                                                       os.path.dirname(__file__), 'lambda')),
                                                   timeout=aws_cdk.Duration.minutes(
                                                       5),
                                                   initial_policy=[comprehend_policy])

        dynamo_job = aws_stepfunctions_tasks.DynamoPutItem(
            self, "Dynamo Job",
            item={
                'id': aws_stepfunctions_tasks.DynamoAttributeValue.from_string(
                    aws_stepfunctions.JsonPath.string_at('$.id.S')
                ),
                'message': aws_stepfunctions_tasks.DynamoAttributeValue.from_string(
                    aws_stepfunctions.JsonPath.string_at('$.message.S')
                ),
                'sentiment': aws_stepfunctions_tasks.DynamoAttributeValue.from_string(
                    aws_stepfunctions.JsonPath.string_at('$.sentiment.S')
                )
            },
            table=dynamo_table,
            result_path=aws_stepfunctions.JsonPath.string_at(
                '$.output_from_ddb_put'),
        )

        comprehend_job = aws_stepfunctions_tasks.LambdaInvoke(
            self, "Submit Job",
            lambda_function=comprehend_lambda_fn,
            output_path="$.Payload",
        )

        definition = comprehend_job.next(dynamo_job)

        sm = aws_stepfunctions.StateMachine(
            self, "StateMachine",
            definition=definition,
            timeout=Duration.minutes(5),
            state_machine_type=aws_stepfunctions.StateMachineType.EXPRESS
        )

        sf_access_policy_doc = aws_iam.PolicyDocument()

        sf_access_policy_doc.add_statements(aws_iam.PolicyStatement(**{
            "effect": aws_iam.Effect.ALLOW,
            "resources": [dynamo_table.table_arn],
            "actions": [
                "dynamodb:BatchWriteItem",
                "dynamodb:PutItem",
            ]
        }))

        sf_access_policy_doc.add_statements(aws_iam.PolicyStatement(**{
            "effect": aws_iam.Effect.ALLOW,
            "resources": [comprehend_lambda_fn.function_arn],
            "actions": [
                "lambda:InvokeFunction",
            ]
        }))

        sf_access_policy_doc.add_statements(aws_iam.PolicyStatement(**{
            "effect": aws_iam.Effect.ALLOW,
            "resources": [sm.state_machine_arn],
            "actions": [
                "states:StartExecution",
                "states:StartSyncExecution"
            ]
        }))

        api = aws_apigateway.StepFunctionsRestApi(self, "StepFunctionsRestApi",
                                                  state_machine=sm)
        all_resources = api.root.add_resource("sentiment")
        apigw_step_role = aws_iam.Role(self, "ApiGatewayRoleForStepFunctions",
                                       role_name='APIGatewayRoleForStepFunctions',
                                       assumed_by=aws_iam.ServicePrincipal(
                                           'apigateway.amazonaws.com'),
                                       inline_policies={
                                           'StepRights': sf_access_policy_doc
                                       },
                                       )

        get_response_templates = '''
            #set($inputRoot = $input.path('$.output'))
            {
            "httpStatusCode": $util.parseJson($inputRoot).output_from_ddb_put.SdkHttpMetadata.HttpStatusCode,
            "Message": $util.parseJson($inputRoot).message.S,
            "Sentiment": $util.parseJson($inputRoot).sentiment.S
            }
            '''

        apigw_error_responses = [
            aws_apigateway.IntegrationResponse(
                status_code="400", selection_pattern="4\d{2}"),
            aws_apigateway.IntegrationResponse(
                status_code="500", selection_pattern="5\d{2}")
        ]

        apigw_ok_responses = [
            aws_apigateway.IntegrationResponse(
                status_code="200",
                response_templates={
                    'application/json': get_response_templates
                }
            )
        ]

        integration_responses = [
            *apigw_ok_responses,
            *apigw_error_responses
        ]

        sf_options = aws_apigateway.IntegrationOptions(
            credentials_role=apigw_step_role,
            integration_responses=integration_responses,
            request_templates={
                "application/json": json.dumps({
                    "TableName": table_name,
                    "input": json.dumps({
                        "id": {
                            "S": "$input.path('$.id')"
                        },
                        "message": {
                            "S": "$input.path('$.message')"
                        }
                    }),
                    "stateMachineArn": "{}".format(sm.state_machine_arn)
                })
            }
        )

        create_integration = aws_apigateway.AwsIntegration(
            service='states',
            action='StartSyncExecution',
            integration_http_method='POST',
            options=sf_options,
        )
        method_responses = [
            aws_apigateway.MethodResponse(status_code='200'),
            aws_apigateway.MethodResponse(status_code='400'),
            aws_apigateway.MethodResponse(status_code='500')
        ]
        all_resources.add_method(
            'POST', integration=create_integration, method_responses=method_responses)
        
        CfnOutput(self, "LambdaFunctionName",
                  value=comprehend_lambda_fn.function_name,
                  export_name='FunctionName',
                  description='Function name')

        CfnOutput(self, "database arn",
                  value=dynamo_table.table_arn,
                  export_name='DynamoDbArn',
                  description='DynamoDBArn')

        CfnOutput(self, "step functions arn",
                  value=sm.state_machine_arn,
                  export_name='StepFunctionArn',
                  description='StepFunctionArn')


app = aws_cdk.App()
GateWayStepFunction(app, "GateWayStepFunction", env=aws_cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION')))
app.synth()
