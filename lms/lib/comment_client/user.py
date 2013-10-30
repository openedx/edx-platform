from .utils import merge_dict, perform_request, CommentClientRequestError

import models
import settings


class User(models.Model):

    accessible_fields = ['username', 'email', 'follower_ids', 'upvoted_ids', 'downvoted_ids',
                         'id', 'external_id', 'subscribed_user_ids', 'children', 'course_id',
                         'subscribed_thread_ids', 'subscribed_commentable_ids',
                         'subscribed_course_ids', 'threads_count', 'comments_count',
                         'default_sort_key'
                        ]

    updatable_fields = ['username', 'external_id', 'email', 'default_sort_key']
    initializable_fields = updatable_fields

    base_url = "{prefix}/users".format(prefix=settings.PREFIX)
    default_retrieve_params = {'complete': True}
    type = 'user'

    @classmethod
    def from_django_user(cls, user):
        return cls(id=str(user.id),
                   external_id=str(user.id),
                   username=user.username,
                   email=user.email)

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
            raise CommentClientRequestError("Can only vote / unvote for threads or comments")
        params = {'user_id': self.id, 'value': value}
        request = perform_request('put', url, params)
        voteable.update_attributes(request)

    def unvote(self, voteable):
        if voteable.type == 'thread':
            url = _url_for_vote_thread(voteable.id)
        elif voteable.type == 'comment':
            url = _url_for_vote_comment(voteable.id)
        else:
            raise CommentClientRequestError("Can only vote / unvote for threads or comments")
        params = {'user_id': self.id}
        request = perform_request('delete', url, params)
        voteable.update_attributes(request)

    def active_threads(self, query_params={}):
        if not self.course_id:
            raise CommentClientRequestError("Must provide course_id when retrieving active threads for the user")
        url = _url_for_user_active_threads(self.id)
        params = {'course_id': self.course_id}
        params = merge_dict(params, query_params)
        response = perform_request('get', url, params)
        return response.get('collection', []), response.get('page', 1), response.get('num_pages', 1)

    def subscribed_threads(self, query_params={}):
        if not self.course_id:
            raise CommentClientRequestError("Must provide course_id when retrieving subscribed threads for the user")
        url = _url_for_user_subscribed_threads(self.id)
        params = {'course_id': self.course_id}
        params = merge_dict(params, query_params)
        response = perform_request('get', url, params)
        return response.get('collection', []), response.get('page', 1), response.get('num_pages', 1)

    def _retrieve(self, *args, **kwargs):
        url = self.url(action='get', params=self.attributes)
        retrieve_params = self.default_retrieve_params
        if self.attributes.get('course_id'):
            retrieve_params['course_id'] = self.course_id
        response = perform_request('get', url, retrieve_params)
        self.update_attributes(**response)


def _url_for_vote_comment(comment_id):
    return "{prefix}/comments/{comment_id}/votes".format(prefix=settings.PREFIX, comment_id=comment_id)


def _url_for_vote_thread(thread_id):
    return "{prefix}/threads/{thread_id}/votes".format(prefix=settings.PREFIX, thread_id=thread_id)


def _url_for_subscription(user_id):
    return "{prefix}/users/{user_id}/subscriptions".format(prefix=settings.PREFIX, user_id=user_id)


def _url_for_user_active_threads(user_id):
    return "{prefix}/users/{user_id}/active_threads".format(prefix=settings.PREFIX, user_id=user_id)


def _url_for_user_subscribed_threads(user_id):
    return "{prefix}/users/{user_id}/subscribed_threads".format(prefix=settings.PREFIX, user_id=user_id)

def _url_for_user_stats(user_id,course_id):
    return "{prefix}/users/{user_id}/stats?course_id={course_id}".format(prefix=settings.PREFIX, user_id=user_id,course_id=course_id)


