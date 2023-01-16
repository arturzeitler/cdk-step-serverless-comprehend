import os
import boto3
import json

ESCALATION_INTENT_MESSAGE = "Seems that you are having troubles with our service. Would you like to be transferred to the associate?"
FULFILMENT_CLOSURE_MESSAGE = "No Problem"

escalation_intent_name = os.getenv('ESCALATION_INTENT_NAME', None)

client = boto3.client('comprehend')


def lambda_handler(event, context):
    # input = json.dumps(event['body'])
    # input = json.loads(input)
    print(event)
    input = json.loads(event['input'])
    print(input)
    req = {
        "messageVersion": "1.0",
        "invocationSource": "DialogCodeHook",
        "userId": "1234567890",
        "sessionAttributes": {},
        "bot": {
            "name": "BookSomething",
            "alias": "None",
            "version": "$LATEST"
        },
        "outputDialogMode": "Text",
        "currentIntent": {
            "name": "BookSomething",
            "slots": {
                    "slot1": "None",
                    "slot2": "None"
            },
            "confirmationStatus": "None"
        },
        "inputTranscript": "{}".format(event['input'])
    }
    print(req)
    sentiment = client.detect_sentiment(
        Text=req['inputTranscript'], LanguageCode='en')['Sentiment']
    # sentiment = client.detect_sentiment(
    #    Text=event['inputTranscript'], LanguageCode='en')['Sentiment']
    if sentiment == 'NEGATIVE':
        event['sentiment'] = ESCALATION_INTENT_MESSAGE
    else:
        event['sentiment'] = FULFILMENT_CLOSURE_MESSAGE
    return event

    '''
    if sentiment == 'NEGATIVE':
        return {
            "statusCode": 200,
            "isBase64Encoded": False,
            'headers': {'Content-Type': 'application/json'},
            "multiValueHeaders": {},
            'body': json.dumps(ESCALATION_INTENT_MESSAGE)
        }
    else:
        return {
            "statusCode": 200,
            "isBase64Encoded": False,
            'headers': {'Content-Type': 'application/json'},
            "multiValueHeaders": {},
            'body': json.dumps(FULFILMENT_CLOSURE_MESSAGE),
        }
    '''
