import json
import logging
import requests
import settings

log = logging.getLogger('mitx.' + __name__)

def strip_none(dic):
    return dict([(k, v) for k, v in dic.iteritems() if v is not None])

def strip_blank(dic):
    def _is_blank(v):
        return isinstance(v, str) and len(v.strip()) == 0
    return dict([(k, v) for k, v in dic.iteritems() if not _is_blank(v)])

def extract(dic, keys):
    if isinstance(keys, str):
        return strip_none({keys: dic.get(keys)})
    else:
        return strip_none({k: dic.get(k) for k in keys})

def merge_dict(dic1, dic2):
    return dict(dic1.items() + dic2.items())

def perform_request(method, url, data_or_params=None, *args, **kwargs):
    if data_or_params is None:
        data_or_params = {}
    data_or_params['api_key'] = settings.API_KEY
    try:
        if method in ['post', 'put', 'patch']:
            response = requests.request(method, url, data=data_or_params)
        else:
            response = requests.request(method, url, params=data_or_params)
    except Exception as err:
        log.exception("Trying to call {method} on {url} with params {params}".format(
            method=method, url=url, params=data_or_params))
        # Reraise with a single exception type 
        raise CommentClientError(str(err))

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
