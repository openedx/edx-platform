import requests
import json
import models

from utils import *

SERVICE_HOST = 'http://localhost:4567'

PREFIX = SERVICE_HOST + '/api/v1'

class Comment(models.Model):
    accessible_fields = [
        'id', 'body', 'anonymous', 'course_id',
        'endorsed', 'parent_id', 'thread_id',
        'username', 'votes', 'user_id', 'closed',
        'created_at', 'updated_at', 'depth',
        'at_position_list',
    ]
    base_url = "{prefix}/comments".format(prefix=PREFIX)
    type = 'comment'


class Thread(models.Model):
    accessible_fields = [
        'id', 'title', 'body', 'anonymous',
        'course_id', 'closed', 'tags', 'votes',
        'commentable_id', 'username', 'user_id',
        'created_at', 'updated_at', 'comments_count',
        'at_position_list', 'children',
    ]
    base_url = "{prefix}/threads".format(prefix=PREFIX)
    default_retrieve_params = {'recursive': False}
    type = 'thread'

    @classmethod
    def search(cls, query_params, *args, **kwargs):
        default_params = {'page': 1,
                          'per_page': 20,
                          'course_id': query_params['course_id'],
                          'recursive': False}
        params = merge_dict(default_params, strip_none(query_params))
        if query_params['text'] or query_params['tags']:
            url = cls.url(action='search')
        else:
            url = cls.url(action='get_all', commentable_id=params['commentable_id'])
            del params['commentable_id']
        response = perform_request('get', url, params, *args, **kwargs)
        return response.get('collection', []), response.get('page', 1), response.get('num_pages', 1)
        
    @classmethod
    def url_for_threads(cls, *args, **kwargs):
        return "{prefix}/{commentable_id}/threads".format(prefix=PREFIX, commentable_id=kwargs.get('commentable_id'))

    @classmethod
    def url_for_search_threads(cls, *args, **kwargs):
        return "{prefix}/search/threads".format(prefix=PREFIX)

    @classmethod
    def url(cls, *args, **kwargs):
        action = kwargs.get('action')
        if action in ['get_all', 'post']:
            return cls.url_for_threads(commentable_id=kwargs.get('commentable_id'))
        elif action == 'search':
            return cls.url_for_search_threads()
        else:
            return super(Thread, cls).url(*args, **kwargs)

    def _retrieve(self, *args, **kwargs):
        url = self.url(action='get', id=self.id)
        response = perform_request('get', url, {'recursive': kwargs.get('recursive')})
        self.update_attributes(**response)

class Commentable(models.Model):

    base_url = "{prefix}/commentables".format(prefix=PREFIX)
    type = 'commentable'

class User(models.Model):

    accessible_fields = ['username', 'follower_ids', 'upvoted_ids', 'downvoted_ids',
                         'id', 'external_id', 'subscribed_user_ids', 'children',
                         'subscribed_thread_ids', 'subscribed_commentable_ids',
                        ]
    base_url = "{prefix}/users".format(prefix=PREFIX)
    default_retrieve_params = {'complete': True}
    type = 'user'

    @classmethod
    def from_django_user(cls, user):
        return cls(id=str(user.id))

    def follow(self, source):
        params = {'source_type': source.type, 'source_id': source.id}
        response = perform_request('post', _url_for_subscription(self.id), params)

    def unfollow(self, source):
        params = {'source_type': source.type, 'source_id': source.id}
        response = perform_request('delete', _url_for_subscription(self.id), params)

    def vote(self, voteable, value):
        if voteable.type == 'thread':
            url = _url_for_vote_thread(voteable.id)
        elif voteable.type == 'comment':
            url = _url_for_vote_comment(voteable.id)
        else:
            raise CommentClientError("Can only vote / unvote for threads or comments")
        params = {'user_id': self.id, 'value': value}
        request = perform_request('put', url, params)
        voteable.update_attributes(request)

    def unvote(self, voteable):
        if voteable.type == 'thread':
            url = _url_for_vote_thread(voteable.id)
        elif voteable.type == 'comment':
            url = _url_for_vote_comment(voteable.id)
        else:
            raise CommentClientError("Can only vote / unvote for threads or comments")
        params = {'user_id': self.id}
        request = perform_request('delete', url, params)
        voteable.update_attributes(request)

def search_similar_threads(course_id, recursive=False, query_params={}, *args, **kwargs):
    default_params = {'course_id': course_id, 'recursive': recursive}
    attributes = dict(default_params.items() + query_params.items())
    return perform_request('get', _url_for_search_similar_threads(), attributes, *args, **kwargs)

def search_recent_active_threads(course_id, recursive=False, query_params={}, *args, **kwargs):
    default_params = {'course_id': course_id, 'recursive': recursive}
    attributes = dict(default_params.items() + query_params.items())
    return perform_request('get', _url_for_search_recent_active_threads(), attributes, *args, **kwargs)

def search_trending_tags(course_id, query_params={}, *args, **kwargs):
    default_params = {'course_id': course_id}
    attributes = dict(default_params.items() + query_params.items())
    return perform_request('get', _url_for_search_trending_tags(), attributes, *args, **kwargs)

def _url_for_search_similar_threads():
    return "{prefix}/search/threads/more_like_this".format(prefix=PREFIX)

def _url_for_search_recent_active_threads():
    return "{prefix}/search/threads/recent_active".format(prefix=PREFIX)

def _url_for_search_trending_tags():
    return "{prefix}/search/tags/trending".format(prefix=PREFIX)

def _url_for_subscription(user_id):
    return "{prefix}/users/{user_id}/subscriptions".format(prefix=PREFIX, user_id=user_id)

def _url_for_vote_comment(comment_id):
    return "{prefix}/comments/{comment_id}/votes".format(prefix=PREFIX, comment_id=comment_id)

def _url_for_vote_thread(thread_id):
    return "{prefix}/threads/{thread_id}/votes".format(prefix=PREFIX, thread_id=thread_id)
