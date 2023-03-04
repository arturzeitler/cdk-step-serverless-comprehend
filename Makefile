post:
	curl -d '{"id":"1", "message":"Great mood"}' -H "Content-Type: application/json" -X POST https://{apiGatewayURL}/{stageName}/sentiment

codepipeline:
	cdk deploy CodePipeline --require-approval never

destroy-serverless:
	cdk destroy GateWayStepFunction

destroy-codepipeline:
	cdk destroy CodePipeline