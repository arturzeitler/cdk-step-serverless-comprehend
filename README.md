# Api Gateway, Lambda, DynamoDB, Step Function

Simple serverless endpoint that call Api Gateway which triggers a state machine that invokes a lambda calling AWS Comprehend to get sentiment of provided message and stores message and sentiment in DynamoDB table before returning sentiment to user.

readme to be completed

```
cdk synth
```

```
cdk deploy --require-approval never
```

```
cdk destroy
```

Example
```
make post
curl -d '{"id":"1", "message":"Great mood"}' -H "Content-Type: application/json" -X POST https://p62aesq267.execute-api.eu-central-1.amazonaws.com/prod/sentiment

                        {
            "httpStatusCode": 200,
            "Message": Great mood,
            "Sentiment": No Problem
            }
```


