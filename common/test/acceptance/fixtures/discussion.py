"""
Tools for creating discussion content fixture data.
"""


import json
from datetime import datetime

import factory
import requests

from common.test.acceptance.fixtures import COMMENTS_STUB_URL
from common.test.acceptance.fixtures.config import ConfigModelFixture


class ContentFactory(factory.Factory):
    class Meta(object):
        model = dict

    id = None
    user_id = "1234"
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

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        # The discussion code assumes that user_id is a string. This ensures that it always will be.
        if 'user_id' in kwargs:
            kwargs['user_id'] = str(kwargs['user_id'])
        return kwargs


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
    context = "course"


class Comment(ContentFactory):
    thread_id = "dummy thread"
    depth = 0
    type = "comment"
    body = "dummy comment body"


class Response(Comment):
    depth = 1
    body = "dummy response body"


class SearchResult(factory.Factory):
    class Meta(object):
        model = dict

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
        return requests.put(
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


class MultipleThreadFixture(DiscussionContentFixture):

    def __init__(self, threads):
        self.threads = threads

    def get_config_data(self):
        threads_list = {thread['id']: thread for thread in self.threads}
        return {"threads": json.dumps(threads_list), "comments": '{}'}

    def add_response(self, response, comments, thread):
        """
        Add responses to the thread
        """
        response['children'] = comments
        if thread["thread_type"] == "discussion":
            response_list_attr = "children"
        elif response["endorsed"]:
            response_list_attr = "endorsed_responses"
        else:
            response_list_attr = "non_endorsed_responses"
        thread.setdefault(response_list_attr, []).append(response)
        thread['comments_count'] += len(comments) + 1


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


class ForumsConfigMixin(object):
    """Mixin providing a method used to configure the forums integration."""
    def enable_forums(self, is_enabled=True):
        """Configures whether or not forums are enabled."""
        ConfigModelFixture('/config/forums', {
            'enabled': is_enabled,
        }).install()
