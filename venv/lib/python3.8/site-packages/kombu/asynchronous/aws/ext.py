"""Amazon boto3 interface."""

try:
    import boto3
    from botocore import exceptions
    from botocore.awsrequest import AWSRequest
    from botocore.response import get_response
except ImportError:
    boto3 = None

    class _void:
        pass

    class BotoCoreError(Exception):
        pass
    exceptions = _void()
    exceptions.BotoCoreError = BotoCoreError
    AWSRequest = _void()
    get_response = _void()


__all__ = (
    'exceptions', 'AWSRequest', 'get_response'
)
