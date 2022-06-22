import logging # To Import
import boto # To Import
from botocore.exceptions import ClientError # To Import
import os # To Import
import requests # To Import
from cms.envs import common # To Import
from uuid import uuid4 # To Import


def upload_to_s3(file):
    url = f"https://{common.AWS_S3_CUSTOM_DOMAIN}"
    uuid = uuid4()
    files = {'file':file}
    key = f"media/{uuid}/{file.name}"
    requests.post(url, data={'key':key, 'overwrite':False}, files=files)
    url_save = f"{url}/{key}"
    return url_save
                    
