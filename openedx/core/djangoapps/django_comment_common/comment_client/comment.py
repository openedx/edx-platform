# pylint: disable=missing-docstring,protected-access
from bs4 import BeautifulSoup

from openedx.core.djangoapps.django_comment_common.comment_client import models, settings

from .thread import Thread, _url_for_flag_abuse_thread, _url_for_unflag_abuse_thread
from .utils import CommentClientRequestError, get_course_key, perform_request
from forum import api as forum_api
from lms.djangoapps.discussion.toggles import is_forum_v2_enabled


class Comment(models.Model):

    accessible_fields = [
        'id', 'body', 'anonymous', 'anonymous_to_peers', 'course_id',
        'endorsed', 'parent_id', 'thread_id', 'username', 'votes', 'user_id',
        'closed', 'created_at', 'updated_at', 'depth', 'at_position_list',
        'type', 'commentable_id', 'abuse_flaggers', 'endorsement',
        'child_count', 'edit_history',
    ]

    updatable_fields = [
        'body', 'anonymous', 'anonymous_to_peers', 'course_id', 'closed',
        'user_id', 'endorsed', 'endorsement_user_id', 'edit_reason_code',
        'closing_user_id', 'editing_user_id',
    ]

    initializable_fields = updatable_fields

    metrics_tag_fields = ['course_id', 'endorsed', 'closed']

    base_url = f"{settings.PREFIX}/comments"
    type = 'comment'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
    def url_for_comments(cls, params=None):
        if params and params.get('parent_id'):
            return _url_for_comment(params['parent_id'])
        else:
            return _url_for_thread_comments(params['thread_id'])

    @classmethod
    def url(cls, action, params=None):
        if params is None:
            params = {}
        if action in ['post']:
            return cls.url_for_comments(params)
        else:
            return super().url(action, params)

    def flagAbuse(self, user, voteable):
        if voteable.type == 'thread':
            url = _url_for_flag_abuse_thread(voteable.id)
        elif voteable.type == 'comment':
            url = _url_for_flag_abuse_comment(voteable.id)
        else:
            raise CommentClientRequestError("Can only flag/unflag threads or comments")
        course_key = get_course_key(self.attributes.get("course_id"))
        if is_forum_v2_enabled(course_key):
            if voteable.type == 'thread':
                response = forum_api.update_thread_flag(voteable.id, "flag", user.id, str(course_key))
            else:
                response = forum_api.update_comment_flag(voteable.id, "flag", user.id, str(course_key))
        else:
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
        course_key = get_course_key(self.attributes.get("course_id"))
        if is_forum_v2_enabled(course_key):
            if voteable.type == "thread":
                response = forum_api.update_thread_flag(
                    thread_id=voteable.id,
                    action="unflag",
                    user_id=user.id,
                    update_all=bool(removeAll),
                    course_id=str(course_key)
                )
            else:
                response = forum_api.update_comment_flag(
                    comment_id=voteable.id,
                    action="unflag",
                    user_id=user.id,
                    update_all=bool(removeAll),
                    course_id=str(course_key)
                )
        else:
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

    @property
    def body_text(self):
        """
        Return the text content of the comment html body.
        """
        soup = BeautifulSoup(self.body, 'html.parser')
        return soup.get_text()


def _url_for_thread_comments(thread_id):
    return f"{settings.PREFIX}/threads/{thread_id}/comments"


def _url_for_comment(comment_id):
    return f"{settings.PREFIX}/comments/{comment_id}"


def _url_for_flag_abuse_comment(comment_id):
    return f"{settings.PREFIX}/comments/{comment_id}/abuse_flag"


def _url_for_unflag_abuse_comment(comment_id):
    return f"{settings.PREFIX}/comments/{comment_id}/abuse_unflag"
