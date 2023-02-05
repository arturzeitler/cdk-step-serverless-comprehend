post:
	curl -d '{"id":"1", "message":"Great mood"}' -H "Content-Type: application/json" -X POST https://{apiGatewayURL}/{stageName}/sentiment
