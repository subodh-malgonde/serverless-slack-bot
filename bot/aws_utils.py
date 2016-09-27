import boto3
import os
import json


def publish_sns_event(function_name, function_args):
    boto_session = boto3.Session(aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                                 aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'), region_name='us-east-1')
    client = boto_session.client('sns')
    data = {"function_name": function_name, "args": function_args}
    message = json.dumps(data)
    topic_arn = os.environ.get('AWS_SNS_ARN')
    client.publish(TopicArn=topic_arn, Message=message)


