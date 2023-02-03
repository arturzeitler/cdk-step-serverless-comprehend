import boto3
import json

ESCALATION_INTENT_MESSAGE = "Problem indeed"
FULFILMENT_CLOSURE_MESSAGE = "No Problem"

client = boto3.client('comprehend')


def lambda_handler(event, context):
    input = json.dumps(event['message']['S'])
    sentiment = client.detect_sentiment(
        Text=input, LanguageCode='en')['Sentiment']
    if sentiment == 'NEGATIVE':
        event['sentiment'] = {
            "S": ESCALATION_INTENT_MESSAGE
        }
    else:
        event['sentiment'] = {
            "S": FULFILMENT_CLOSURE_MESSAGE
        }
    return event
