"""Amazon SQS boto3 interface."""


try:
    import boto3
except ImportError:
    boto3 = None
