# pylint: disable=missing-docstring,protected-access
import logging
import time

from bs4 import BeautifulSoup

from openedx.core.djangoapps.django_comment_common.comment_client import models, settings

from .thread import Thread
from .utils import CommentClientRequestError, get_course_key
from forum import api as forum_api
from forum.backends.mongodb.comments import Comment as ForumComment


log = logging.getLogger(__name__)


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

    def flagAbuse(self, user, voteable, course_id=None):
        if voteable.type != 'comment':
            raise CommentClientRequestError("Can only flag comments")

        course_key = get_course_key(self.attributes.get("course_id") or course_id)
        response = forum_api.update_comment_flag(
            comment_id=voteable.id,
            action="flag",
            user_id=str(user.id),
            course_id=str(course_key),
        )
        voteable._update_from_response(response)

    def unFlagAbuse(self, user, voteable, removeAll, course_id=None):
        if voteable.type != 'comment':
            raise CommentClientRequestError("Can only unflag comments")

        course_key = get_course_key(self.attributes.get("course_id") or course_id)
        response = forum_api.update_comment_flag(
            comment_id=voteable.id,
            action="unflag",
            user_id=str(user.id),
            update_all=bool(removeAll),
            course_id=str(course_key),
        )
        voteable._update_from_response(response)

    @property
    def body_text(self):
        """
        Return the text content of the comment html body.
        """
        soup = BeautifulSoup(self.body, 'html.parser')
        return soup.get_text()

    @classmethod
    def get_user_comment_count(cls, user_id, course_ids):
        """
        Returns comments and responses count of user in the given course_ids.
        TODO: Add support for MySQL backend as well
        """
        query_params = {
            "course_id": {"$in": course_ids},
            "author_id": str(user_id),
            "_type": "Comment"
        }
        return ForumComment()._collection.count_documents(query_params)  # pylint: disable=protected-access

    @classmethod
    def delete_user_comments(cls, user_id, course_ids):
        """
        Deletes comments and responses of user in the given course_ids.
        TODO: Add support for MySQL backend as well
        """
        start_time = time.time()
        query_params = {
            "course_id": {"$in": course_ids},
            "author_id": str(user_id),
        }
        comments_deleted = 0
        comments = ForumComment().get_list(**query_params)
        log.info(f"<<Bulk Delete>> Fetched comments for user {user_id} in {time.time() - start_time} seconds")
        for comment in comments:
            start_time = time.time()
            comment_id = comment.get("_id")
            course_id = comment.get("course_id")
            if comment_id:
                forum_api.delete_comment(comment_id, course_id=course_id)
                comments_deleted += 1
            log.info(f"<<Bulk Delete>> Deleted comment {comment_id} in {time.time() - start_time} seconds."
                     f" Comment Found: {comment_id is not None}")
        return comments_deleted


def _url_for_thread_comments(thread_id):
    return f"{settings.PREFIX}/threads/{thread_id}/comments"


def _url_for_comment(comment_id):
    return f"{settings.PREFIX}/comments/{comment_id}"


def _url_for_flag_abuse_comment(comment_id):
    return f"{settings.PREFIX}/comments/{comment_id}/abuse_flag"


def _url_for_unflag_abuse_comment(comment_id):
    return f"{settings.PREFIX}/comments/{comment_id}/abuse_unflag"
