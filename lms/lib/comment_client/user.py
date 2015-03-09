""" User model wrapper for comment service"""
from .utils import merge_dict, perform_request, CommentClientRequestError, CommentClientPaginatedResult

import models
import settings


class User(models.Model):

    accessible_fields = [
        'username', 'follower_ids', 'upvoted_ids', 'downvoted_ids',
        'id', 'external_id', 'subscribed_user_ids', 'children', 'course_id',
        'group_id', 'subscribed_thread_ids', 'subscribed_commentable_ids',
        'subscribed_course_ids', 'threads_count', 'comments_count',
        'default_sort_key'
    ]

    updatable_fields = ['username', 'external_id', 'default_sort_key']
    initializable_fields = updatable_fields

    metric_tag_fields = ['course_id']

    base_url = "{prefix}/users".format(prefix=settings.PREFIX)
    default_retrieve_params = {'complete': True}
    type = 'user'

    @classmethod
    def from_django_user(cls, user):
        return cls(id=str(user.id),
                   external_id=str(user.id),
                   username=user.username)

    def read(self, source):
        """
        Calls cs_comments_service to mark thread as read for the user
        """
        params = {'source_type': source.type, 'source_id': source.id}
        perform_request(
            'post',
            _url_for_read(self.id),
            params,
            metric_action='user.read',
            metric_tags=self._metric_tags + ['target.type:{}'.format(source.type)],
        )

    def follow(self, source):
        params = {'source_type': source.type, 'source_id': source.id}
        response = perform_request(
            'post',
            _url_for_subscription(self.id),
            params,
            metric_action='user.follow',
            metric_tags=self._metric_tags + ['target.type:{}'.format(source.type)],
        )

    def unfollow(self, source):
        params = {'source_type': source.type, 'source_id': source.id}
        response = perform_request(
            'delete',
            _url_for_subscription(self.id),
            params,
            metric_action='user.unfollow',
            metric_tags=self._metric_tags + ['target.type:{}'.format(source.type)],
        )

    def vote(self, voteable, value):
        if voteable.type == 'thread':
            url = _url_for_vote_thread(voteable.id)
        elif voteable.type == 'comment':
            url = _url_for_vote_comment(voteable.id)
        else:
            raise CommentClientRequestError("Can only vote / unvote for threads or comments")
        params = {'user_id': self.id, 'value': value}
        response = perform_request(
            'put',
            url,
            params,
            metric_action='user.vote',
            metric_tags=self._metric_tags + ['target.type:{}'.format(voteable.type)],
        )
        voteable._update_from_response(response)

    def unvote(self, voteable):
        if voteable.type == 'thread':
            url = _url_for_vote_thread(voteable.id)
        elif voteable.type == 'comment':
            url = _url_for_vote_comment(voteable.id)
        else:
            raise CommentClientRequestError("Can only vote / unvote for threads or comments")
        params = {'user_id': self.id}
        response = perform_request(
            'delete',
            url,
            params,
            metric_action='user.unvote',
            metric_tags=self._metric_tags + ['target.type:{}'.format(voteable.type)],
        )
        voteable._update_from_response(response)

    def active_threads(self, query_params={}):
        if not self.course_id:
            raise CommentClientRequestError("Must provide course_id when retrieving active threads for the user")
        url = _url_for_user_active_threads(self.id)
        params = {'course_id': self.course_id.to_deprecated_string()}
        params = merge_dict(params, query_params)
        response = perform_request(
            'get',
            url,
            params,
            metric_action='user.active_threads',
            metric_tags=self._metric_tags,
            paged_results=True,
        )
        return response.get('collection', []), response.get('page', 1), response.get('num_pages', 1)

    def subscribed_threads(self, query_params={}):
        if not self.course_id:
            raise CommentClientRequestError("Must provide course_id when retrieving subscribed threads for the user")
        url = _url_for_user_subscribed_threads(self.id)
        params = {'course_id': self.course_id.to_deprecated_string()}
        params = merge_dict(params, query_params)
        response = perform_request(
            'get',
            url,
            params,
            metric_action='user.subscribed_threads',
            metric_tags=self._metric_tags,
            paged_results=True
        )
        return CommentClientPaginatedResult(
            collection=response.get('collection', []),
            page=response.get('page', 1),
            num_pages=response.get('num_pages', 1),
            thread_count=response.get('thread_count', 0)
        )

    def social_stats(self, end_date=None):
        return get_user_social_stats(self.id, self.course_id, end_date=end_date)

    @classmethod
    def all_social_stats(cls, course_id, end_date=None, thread_type=None):
        """ Get social stats for all users participating in a course """
        return get_user_social_stats('*', course_id, end_date=end_date, thread_type=thread_type)

    def _retrieve(self, *args, **kwargs):
        url = self.url(action='get', params=self.attributes)
        retrieve_params = self.default_retrieve_params.copy()
        retrieve_params.update(kwargs)
        if self.attributes.get('course_id'):
            retrieve_params['course_id'] = self.course_id.to_deprecated_string()
        if self.attributes.get('group_id'):
            retrieve_params['group_id'] = self.group_id
        try:
            response = perform_request(
                'get',
                url,
                retrieve_params,
                metric_action='model.retrieve',
                metric_tags=self._metric_tags,
            )
        except CommentClientRequestError as e:
            if e.status_code == 404:
                # attempt to gracefully recover from a previous failure
                # to sync this user to the comments service.
                self.save()
                response = perform_request(
                    'get',
                    url,
                    retrieve_params,
                    metric_action='model.retrieve',
                    metric_tags=self._metric_tags,
                )
            else:
                raise
        self._update_from_response(response)


def get_user_social_stats(user_id, course_id, end_date=None, thread_type=None):
    """ Queries cs_comments_service for social_stats """
    if not course_id:
        raise CommentClientRequestError("Must provide course_id when retrieving social stats for the user")

    url = _url_for_user_social_stats(user_id)
    params = {'course_id': course_id}
    if end_date:
        params.update({'end_date': end_date.isoformat()})
    if thread_type:
        params.update({'thread_type': thread_type})

    response = perform_request(
        'get',
        url,
        params
    )
    return response


def get_course_social_stats(course_id, end_date=None):
    """
    Helper method to get the social stats from the comment service
    """
    url = _url_for_course_social_stats(end_date=end_date)
    params = {'course_id': course_id}
    if end_date:
        params.update({'end_date': end_date.isoformat()})

    response = perform_request(
        'get',
        url,
        params
    )
    return response

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


def _url_for_user_social_stats(user_id, end_date=None):
    return "{prefix}/users/{user_id}/social_stats".format(prefix=settings.PREFIX, user_id=user_id)


def _url_for_course_social_stats(end_date=None):
    return "{prefix}/users/*/social_stats".format(prefix=settings.PREFIX)


def _url_for_read(user_id):
    """
    Returns cs_comments_service url endpoint to mark thread as read for given user_id
    """
    return "{prefix}/users/{user_id}/read".format(prefix=settings.PREFIX, user_id=user_id)
