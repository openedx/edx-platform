"""" Common utilities for comment client wrapper """
from contextlib import contextmanager
import dogstats_wrapper as dog_stats_api
import logging
import requests
from django.conf import settings
from time import time
from uuid import uuid4
from django.utils.translation import get_language

log = logging.getLogger(__name__)


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


@contextmanager
def request_timer(request_id, method, url, tags=None):
    start = time()
    with dog_stats_api.timer('comment_client.request.time', tags=tags):
        yield
    end = time()
    duration = end - start

    log.info(
        u"comment_client_request_log: request_id={request_id}, method={method}, "
        u"url={url}, duration={duration}".format(
            request_id=request_id,
            method=method,
            url=url,
            duration=duration
        )
    )


def perform_request(method, url, data_or_params=None, raw=False,
                    metric_action=None, metric_tags=None, paged_results=False):
    # To avoid dependency conflict
    from django_comment_common.models import ForumsConfig
    config = ForumsConfig.current()

    if not config.enabled:
        raise CommentClientMaintenanceError('service disabled')

    if metric_tags is None:
        metric_tags = []

    metric_tags.append(u'method:{}'.format(method))
    if metric_action:
        metric_tags.append(u'action:{}'.format(metric_action))

    if data_or_params is None:
        data_or_params = {}
    headers = {
        'X-Edx-Api-Key': config.api_key,
        'Accept-Language': get_language(),
    }
    request_id = uuid4()
    request_id_dict = {'request_id': request_id}

    if method in ['post', 'put', 'patch']:
        data = data_or_params
        params = request_id_dict
    else:
        data = None
        params = merge_dict(data_or_params, request_id_dict)
    with request_timer(request_id, method, url, metric_tags):
        response = requests.request(
            method,
            url,
            data=data,
            params=params,
            headers=headers,
            timeout=config.connection_timeout
        )

    metric_tags.append(u'status_code:{}'.format(response.status_code))
    if response.status_code > 200:
        metric_tags.append(u'result:failure')
    else:
        metric_tags.append(u'result:success')

    dog_stats_api.increment('comment_client.request.count', tags=metric_tags)

    if 200 < response.status_code < 500:
        raise CommentClientRequestError(response.text, response.status_code)
    # Heroku returns a 503 when an application is in maintenance mode
    elif response.status_code == 503:
        raise CommentClientMaintenanceError(response.text)
    elif response.status_code == 500:
        raise CommentClient500Error(response.text)
    else:
        if raw:
            return response.text
        else:
            try:
                data = response.json()
            except ValueError:
                raise CommentClientError(
                    u"Invalid JSON response for request {request_id}; first 100 characters: '{content}'".format(
                        request_id=request_id,
                        content=response.text[:100]
                    )
                )
            if paged_results:
                dog_stats_api.histogram(
                    'comment_client.request.paged.result_count',
                    value=len(data.get('collection', [])),
                    tags=metric_tags
                )
                dog_stats_api.histogram(
                    'comment_client.request.paged.page',
                    value=data.get('page', 1),
                    tags=metric_tags
                )
                dog_stats_api.histogram(
                    'comment_client.request.paged.num_pages',
                    value=data.get('num_pages', 1),
                    tags=metric_tags
                )
            return data


class CommentClientError(Exception):
    def __init__(self, msg):
        self.message = msg

    def __str__(self):
        return repr(self.message)


class CommentClientRequestError(CommentClientError):
    def __init__(self, msg, status_codes=400):
        super(CommentClientRequestError, self).__init__(msg)
        self.status_code = status_codes


class CommentClient500Error(CommentClientError):
    pass


class CommentClientMaintenanceError(CommentClientError):
    pass


class CommentClientPaginatedResult(object):
    """ class for paginated results returned from comment services"""

    def __init__(self, collection, page, num_pages, thread_count=0, corrected_text=None):
        self.collection = collection
        self.page = page
        self.num_pages = num_pages
        self.thread_count = thread_count
        self.corrected_text = corrected_text
