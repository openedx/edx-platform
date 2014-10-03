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
    thread_type = "discussion"
    anonymous = False
    anonymous_to_peers = False
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


class SearchResult(factory.Factory):
    FACTORY_FOR = dict
    discussion_data = []
    annotated_content_info = {}
    num_pages = 1
    page = 1
    corrected_text = None


class DiscussionContentFixture(object):

    def push(self):
        """
        Push the data to the stub comments service.
        """
        requests.put(
            '{}/set_config'.format(COMMENTS_STUB_URL),
            data=self.get_config_data()
        )

    def get_config_data(self):
        """
        return a dictionary with the fixture's data serialized for PUTting to the stub server's config endpoint.
        """
        raise NotImplementedError()


class SingleThreadViewFixture(DiscussionContentFixture):

    def __init__(self, thread):
        self.thread = thread

    def addResponse(self, response, comments=[]):
        response['children'] = comments
        if self.thread["thread_type"] == "discussion":
            responseListAttr = "children"
        elif response["endorsed"]:
            responseListAttr = "endorsed_responses"
        else:
            responseListAttr = "non_endorsed_responses"
        self.thread.setdefault(responseListAttr, []).append(response)
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

    def get_config_data(self):
        return {
            "threads": json.dumps({self.thread['id']: self.thread}),
            "comments": json.dumps(self._get_comment_map())
        }


class UserProfileViewFixture(DiscussionContentFixture):

    def __init__(self, threads):
        self.threads = threads

    def get_config_data(self):
        return {"active_threads": json.dumps(self.threads)}


class SearchResultFixture(DiscussionContentFixture):

    def __init__(self, result):
        self.result = result

    def get_config_data(self):
        return {"search_result": json.dumps(self.result)}
