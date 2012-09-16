from utils import *

from thread import Thread
import models
import settings

class Comment(models.Model):

    accessible_fields = [
        'id', 'body', 'anonymous', 'anonymous_to_peers', 'course_id',
        'endorsed', 'parent_id', 'thread_id', 'username', 'votes', 'user_id',
        'closed', 'created_at', 'updated_at', 'depth', 'at_position_list',
        'type', 'commentable_id',
    ]

    updatable_fields = [
        'body', 'anonymous', 'anonymous_to_peers', 'course_id', 'closed',
        'user_id', 'endorsed',
    ]

    initializable_fields = updatable_fields

    base_url = "{prefix}/comments".format(prefix=settings.PREFIX)
    type = 'comment'

    @property
    def thread(self):
        return Thread(id=self.thread_id, type='thread')

    @classmethod
    def url_for_comments(cls, params={}):
        if params.get('thread_id'):
            return _url_for_thread_comments(params['thread_id'])
        else:
            return _url_for_comment(params['parent_id'])

    @classmethod
    def url(cls, action, params={}):
        if action in ['post']:
            return cls.url_for_comments(params)
        else:
            return super(Comment, cls).url(action, params)

def _url_for_thread_comments(thread_id):
    return "{prefix}/threads/{thread_id}/comments".format(prefix=settings.PREFIX, thread_id=thread_id)

def _url_for_comment(comment_id):
    return "{prefix}/comments/{comment_id}".format(prefix=settings.PREFIX, comment_id=comment_id)
