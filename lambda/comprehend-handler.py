import boto3
import json

ESCALATION_INTENT_MESSAGE = "Seems that you are having troubles with our service. Would you like to be transferred to the associate?"
FULFILMENT_CLOSURE_MESSAGE = "No Problem"

client = boto3.client('comprehend')


def lambda_handler(event, context):
    input = json.dumps(event['input'])
    sentiment = client.detect_sentiment(
        Text=event['input'], LanguageCode='en')['Sentiment']
    if sentiment == 'NEGATIVE':
        event['sentiment'] = ESCALATION_INTENT_MESSAGE
    else:
        event['sentiment'] = FULFILMENT_CLOSURE_MESSAGE
    return event
