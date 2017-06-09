from .utils import CommentClientRequestError, perform_request

from .thread import Thread, _url_for_flag_abuse_thread, _url_for_unflag_abuse_thread
from lms.lib.comment_client import models
from lms.lib.comment_client import settings


class Comment(models.Model):

    accessible_fields = [
        'id', 'body', 'anonymous', 'anonymous_to_peers', 'course_id',
        'endorsed', 'parent_id', 'thread_id', 'username', 'votes', 'user_id',
        'closed', 'created_at', 'updated_at', 'depth', 'at_position_list',
        'type', 'commentable_id', 'abuse_flaggers', 'endorsement',
        'child_count',
    ]

    updatable_fields = [
        'body', 'anonymous', 'anonymous_to_peers', 'course_id', 'closed',
        'user_id', 'endorsed', 'endorsement_user_id',
    ]

    initializable_fields = updatable_fields

    metrics_tag_fields = ['course_id', 'endorsed', 'closed']

    base_url = "{prefix}/comments".format(prefix=settings.PREFIX)
    type = 'comment'

    def __init__(self, *args, **kwargs):
        super(Comment, self).__init__(*args, **kwargs)
        self._cached_thread = None

    @property
    def thread(self):
        if not self._cached_thread:
            self._cached_thread = Thread(id=self.thread_id, type='thread')
        return self._cached_thread

    @property
    def context(self):
        """Return the context of the thread which this comment belongs to."""
        return self.thread.context

    @classmethod
    def url_for_comments(cls, params={}):
        if params.get('parent_id'):
            return _url_for_comment(params['parent_id'])
        else:
            return _url_for_thread_comments(params['thread_id'])

    @classmethod
    def url(cls, action, params={}):
        if action in ['post']:
            return cls.url_for_comments(params)
        else:
            return super(Comment, cls).url(action, params)

    def flagAbuse(self, user, voteable):
        if voteable.type == 'thread':
            url = _url_for_flag_abuse_thread(voteable.id)
        elif voteable.type == 'comment':
            url = _url_for_flag_abuse_comment(voteable.id)
        else:
            raise CommentClientRequestError("Can only flag/unflag threads or comments")
        params = {'user_id': user.id}
        response = perform_request(
            'put',
            url,
            params,
            metric_tags=self._metric_tags,
            metric_action='comment.abuse.flagged'
        )
        voteable._update_from_response(response)

    def unFlagAbuse(self, user, voteable, removeAll):
        if voteable.type == 'thread':
            url = _url_for_unflag_abuse_thread(voteable.id)
        elif voteable.type == 'comment':
            url = _url_for_unflag_abuse_comment(voteable.id)
        else:
            raise CommentClientRequestError("Can flag/unflag for threads or comments")
        params = {'user_id': user.id}

        if removeAll:
            params['all'] = True

        response = perform_request(
            'put',
            url,
            params,
            metric_tags=self._metric_tags,
            metric_action='comment.abuse.unflagged'
        )
        voteable._update_from_response(response)


def _url_for_thread_comments(thread_id):
    return "{prefix}/threads/{thread_id}/comments".format(prefix=settings.PREFIX, thread_id=thread_id)


def _url_for_comment(comment_id):
    return "{prefix}/comments/{comment_id}".format(prefix=settings.PREFIX, comment_id=comment_id)


def _url_for_flag_abuse_comment(comment_id):
    return "{prefix}/comments/{comment_id}/abuse_flag".format(prefix=settings.PREFIX, comment_id=comment_id)


def _url_for_unflag_abuse_comment(comment_id):
    return "{prefix}/comments/{comment_id}/abuse_unflag".format(prefix=settings.PREFIX, comment_id=comment_id)
