import requests
import json

def strip_none(dic):
    def _is_none(v):
        return v is None or (isinstance(v, str) and len(v.strip()) == 0)
    return dict([(k, v) for k, v in dic.iteritems() if not _is_none(v)])

def extract(dic, keys):
    return strip_none({k: dic.get(k) for k in keys})

def merge_dict(dic1, dic2):
    return dict(dic1.items() + dic2.items())
    
def perform_request(method, url, data_or_params=None, *args, **kwargs):
    if method in ['post', 'put', 'patch']:
        response = requests.request(method, url, data=data_or_params)
    else:
        response = requests.request(method, url, params=data_or_params)
    if 200 < response.status_code < 500:
        raise CommentClientError(response.text)
    elif response.status_code == 500:
        raise CommentClientUnknownError(response.text)
    else:
        if kwargs.get("raw", False):
            return response.text
        else:
            return json.loads(response.text)

class CommentClientError(Exception):
    def __init__(self, msg):
        self.message = msg

    def __str__(self):
        return repr(self.message)

class CommentClientUnknownError(CommentClientError):
    pass
