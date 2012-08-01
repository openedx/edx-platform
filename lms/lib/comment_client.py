import requests
import json

SERVICE_HOST = 'http://localhost:4567'

PREFIX = SERVICE_HOST + '/api/v1'

class CommentClientError(Exception):
    def __init__(self, msg):
        self.message = msg

class CommentClientUnknownError(CommentClientError):
    pass

def delete_threads(commentable_id, *args, **kwargs):
    return _perform_request('delete', _url_for_commentable_threads(commentable_id), *args, **kwargs)

def get_threads(commentable_id, recursive=False, page=1, per_page=20, *args, **kwargs):
    response = _perform_request('get', _url_for_threads(commentable_id), {'recursive': recursive, 'page': page, 'per_page': per_page}, *args, **kwargs)
    return response['collection'], response['page'], response['per_page'], response['num_pages']

def get_threads_tags(*args, **kwargs):
    return _perform_request('get', _url_for_threads_tags(), {}, *args, **kwargs)

def tags_autocomplete(value, *args, **kwargs):
    return _perform_request('get', _url_for_threads_tags_autocomplete(), {'value': value}, *args, **kwargs)

def create_thread(commentable_id, attributes, *args, **kwargs):
    return _perform_request('post', _url_for_threads(commentable_id), attributes, *args, **kwargs)
    
def get_thread(thread_id, recursive=False, *args, **kwargs):
    return _perform_request('get', _url_for_thread(thread_id), {'recursive': recursive}, *args, **kwargs)

def update_thread(thread_id, attributes, *args, **kwargs):
    return _perform_request('put', _url_for_thread(thread_id), attributes, *args, **kwargs)

def create_comment(thread_id, attributes, *args, **kwargs):
    return _perform_request('post', _url_for_thread_comments(thread_id), attributes, *args, **kwargs)

def delete_thread(thread_id, *args, **kwargs):
    return _perform_request('delete', _url_for_thread(thread_id), *args, **kwargs)

def get_comment(comment_id, recursive=False, *args, **kwargs):
    return _perform_request('get', _url_for_comment(comment_id), {'recursive': recursive}, *args, **kwargs)

def update_comment(comment_id, attributes, *args, **kwargs):
    return _perform_request('put', _url_for_comment(comment_id), attributes, *args, **kwargs)

def create_sub_comment(comment_id, attributes, *args, **kwargs):
    return _perform_request('post', _url_for_comment(comment_id), attributes, *args, **kwargs)

def delete_comment(comment_id, *args, **kwargs):
    return _perform_request('delete', _url_for_comment(comment_id), *args, **kwargs)

def vote_for_comment(comment_id, user_id, value, *args, **kwargs):
    return _perform_request('put', _url_for_vote_comment(comment_id), {'user_id': user_id, 'value': value}, *args, **kwargs)

def undo_vote_for_comment(comment_id, user_id, *args, **kwargs):
    return _perform_request('delete', _url_for_vote_comment(comment_id), *args, **kwargs)

def vote_for_thread(thread_id, user_id, value, *args, **kwargs):
    return _perform_request('put', _url_for_vote_thread(thread_id), {'user_id': user_id, 'value': value}, *args, **kwargs)

def undo_vote_for_thread(thread_id, user_id, *args, **kwargs):
    return _perform_request('delete', _url_for_vote_thread(thread_id), *args, **kwargs)

def get_notifications(user_id, *args, **kwargs):
    return _perform_request('get', _url_for_notifications(user_id), *args, **kwargs)

def get_user_info(user_id, complete=True, *args, **kwargs):
    return _perform_request('get', _url_for_user(user_id), {'complete': complete}, *args, **kwargs)

def subscribe(user_id, subscription_detail, *args, **kwargs):
    return _perform_request('post', _url_for_subscription(user_id), subscription_detail, *args, **kwargs)

def subscribe_user(user_id, followed_user_id, *args, **kwargs):
    return subscribe(user_id, {'source_type': 'user', 'source_id': followed_user_id})

follow = subscribe_user

def subscribe_thread(user_id, thread_id, *args, **kwargs):
    return subscribe(user_id, {'source_type': 'thread', 'source_id': thread_id})

def subscribe_commentable(user_id, commentable_id, *args, **kwargs):
    return subscribe(user_id, {'source_type': 'other', 'source_id': commentable_id})

def unsubscribe(user_id, subscription_detail, *args, **kwargs):
    return _perform_request('delete', _url_for_subscription(user_id), subscription_detail, *args, **kwargs)

def unsubscribe_user(user_id, followed_user_id, *args, **kwargs):
    return unsubscribe(user_id, {'source_type': 'user', 'source_id': followed_user_id})

unfollow = unsubscribe_user

def unsubscribe_thread(user_id, thread_id, *args, **kwargs):
    return unsubscribe(user_id, {'source_type': 'thread', 'source_id': thread_id})

def unsubscribe_commentable(user_id, commentable_id, *args, **kwargs):
    return unsubscribe(user_id, {'source_type': 'other', 'source_id': commentable_id})

def search_threads(attributes, *args, **kwargs):
    default_attributes = {'page': 1, 'per_page': 20}
    attributes = dict(default_attributes.items() + attributes.items())
    return _perform_request('get', _url_for_search_threads(), attributes, *args, **kwargs)

def _perform_request(method, url, data_or_params=None, *args, **kwargs):
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

def _url_for_threads(commentable_id):
    return "{prefix}/{commentable_id}/threads".format(prefix=PREFIX, commentable_id=commentable_id)

def _url_for_thread(thread_id):
    return "{prefix}/threads/{thread_id}".format(prefix=PREFIX, thread_id=thread_id)

def _url_for_thread_comments(thread_id):
    return "{prefix}/threads/{thread_id}/comments".format(prefix=PREFIX, thread_id=thread_id)

def _url_for_comment(comment_id):
    return "{prefix}/comments/{comment_id}".format(prefix=PREFIX, comment_id=comment_id)

def _url_for_vote_comment(comment_id):
    return "{prefix}/comments/{comment_id}/votes".format(prefix=PREFIX, comment_id=comment_id)

def _url_for_vote_thread(thread_id):
    return "{prefix}/threads/{thread_id}/votes".format(prefix=PREFIX, thread_id=thread_id)

def _url_for_notifications(user_id):
    return "{prefix}/users/{user_id}/notifications".format(prefix=PREFIX, user_id=user_id)

def _url_for_subscription(user_id):
    return "{prefix}/users/{user_id}/subscriptions".format(prefix=PREFIX, user_id=user_id)

def _url_for_user(user_id):
    return "{prefix}/users/{user_id}".format(prefix=PREFIX, user_id=user_id)

def _url_for_search_threads():
    return "{prefix}/search/threads".format(prefix=PREFIX)

def _url_for_threads_tags():
    return "{prefix}/threads/tags".format(prefix=PREFIX)

def _url_for_threads_tags_autocomplete():
    return "{prefix}/threads/tags/autocomplete".format(prefix=PREFIX)
