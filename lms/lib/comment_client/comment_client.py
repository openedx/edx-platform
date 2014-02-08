# Import other classes here so they can be imported from here.
# pylint: disable=W0611
from .comment import Comment
from .thread import Thread
from .user import User
from .commentable import Commentable

from .utils import perform_request

import settings


def search_similar_threads(course_id, recursive=False, query_params={}, *args, **kwargs):
    default_params = {'course_id': course_id, 'recursive': recursive}
    attributes = dict(default_params.items() + query_params.items())
    return perform_request('get', _url_for_search_similar_threads(), attributes, *args, **kwargs)


def search_recent_active_threads(course_id, recursive=False, query_params={}, *args, **kwargs):
    default_params = {'course_id': course_id, 'recursive': recursive}
    attributes = dict(default_params.items() + query_params.items())
    return perform_request('get', _url_for_search_recent_active_threads(), attributes, *args, **kwargs)


def _url_for_search_similar_threads():
    return "{prefix}/search/threads/more_like_this".format(prefix=settings.PREFIX)


def _url_for_search_recent_active_threads():
    return "{prefix}/search/threads/recent_active".format(prefix=settings.PREFIX)
