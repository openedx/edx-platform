"""
Tools for creating discussion content fixture data.
"""

from datetime import datetime
import json

import factory
import requests

from . import COMMENTS_STUB_URL


class ContentFactory(factory.Factory):
    FACTORY_FOR = dict
    id = None
    user_id = "dummy-user-id"
    username = "dummy-username"
    course_id = "dummy-course-id"
    commentable_id = "dummy-commentable-id"
    anonymous = False
    anonymous_to_peers = False
    at_position_list = []
    abuse_flaggers = []
    created_at = datetime.utcnow().isoformat()
    updated_at = datetime.utcnow().isoformat()
    endorsed = False
    closed = False
    votes = {"up_count": 0}


class Thread(ContentFactory):
    comments_count = 0
    unread_comments_count = 0
    title = "dummy thread title"
    body = "dummy thread body"
    type = "thread"
    group_id = None
    pinned = False
    read = False


class Comment(ContentFactory):
    thread_id = None
    depth = 0
    type = "comment"
    body = "dummy comment body"


class Response(Comment):
    depth = 1
    body = "dummy response body"


class SingleThreadViewFixture(object):

    def __init__(self, thread):
        self.thread = thread

    def addResponse(self, response, comments=[]):
        response['children'] = comments
        self.thread.setdefault('children', []).append(response)
        self.thread['comments_count'] += len(comments) + 1

    def _get_comment_map(self):
        """
        Generate a dict mapping each response/comment in the thread
        by its `id`.
        """
        def _visit(obj):
            res = []
            for child in obj.get('children', []):
                res.append((child['id'], child))
                if 'children' in child:
                    res += _visit(child)
            return res
        return dict(_visit(self.thread))

    def push(self):
        """
        Push the data to the stub comments service.
        """
        requests.put(
            '{}/set_config'.format(COMMENTS_STUB_URL),
            data={
                "threads": json.dumps({self.thread['id']: self.thread}),
                "comments": json.dumps(self._get_comment_map())
            }
        )

class UserProfileViewFixture(object):

    def __init__(self, threads):
        self.threads = threads

    def push(self):
        """
        Push the data to the stub comments service.
        """
        requests.put(
            '{}/set_config'.format(COMMENTS_STUB_URL),
            data={
                "active_threads": json.dumps(self.threads),
            }
        )
