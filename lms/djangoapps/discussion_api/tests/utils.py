"""
Discussion API test utilities
"""
from contextlib import closing
from datetime import datetime
import json
import re

import hashlib
import httpretty
from pytz import UTC
from PIL import Image

from openedx.core.djangoapps.profile_images.images import create_profile_images
from openedx.core.djangoapps.profile_images.tests.helpers import make_image_file
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_names, set_has_profile_image


def _get_thread_callback(thread_data):
    """
    Get a callback function that will return POST/PUT data overridden by
    response_overrides.
    """
    def callback(request, _uri, headers):
        """
        Simulate the thread creation or update endpoint by returning the provided
        data along with the data from response_overrides and dummy values for any
        additional required fields.
        """
        response_data = make_minimal_cs_thread(thread_data)
        for key, val_list in request.parsed_body.items():
            val = val_list[0]
            if key in ["anonymous", "anonymous_to_peers", "closed", "pinned"]:
                response_data[key] = val == "True"
            else:
                response_data[key] = val
        return (200, headers, json.dumps(response_data))

    return callback


def _get_comment_callback(comment_data, thread_id, parent_id):
    """
    Get a callback function that will return a comment containing the given data
    plus necessary dummy data, overridden by the content of the POST/PUT
    request.
    """
    def callback(request, _uri, headers):
        """
        Simulate the comment creation or update endpoint as described above.
        """
        response_data = make_minimal_cs_comment(comment_data)
        # thread_id and parent_id are not included in request payload but
        # are returned by the comments service
        response_data["thread_id"] = thread_id
        response_data["parent_id"] = parent_id
        for key, val_list in request.parsed_body.items():
            val = val_list[0]
            if key in ["anonymous", "anonymous_to_peers", "endorsed"]:
                response_data[key] = val == "True"
            else:
                response_data[key] = val
        return (200, headers, json.dumps(response_data))

    return callback


class CommentsServiceMockMixin(object):
    """Mixin with utility methods for mocking the comments service"""
    def register_get_threads_response(self, threads, page, num_pages):
        """Register a mock response for GET on the CS thread list endpoint"""
        httpretty.register_uri(
            httpretty.GET,
            "http://localhost:4567/api/v1/threads",
            body=json.dumps({
                "collection": threads,
                "page": page,
                "num_pages": num_pages,
                "thread_count": len(threads),
            }),
            status=200
        )

    def register_get_threads_search_response(self, threads, rewrite, num_pages=1):
        """Register a mock response for GET on the CS thread search endpoint"""
        httpretty.register_uri(
            httpretty.GET,
            "http://localhost:4567/api/v1/search/threads",
            body=json.dumps({
                "collection": threads,
                "page": 1,
                "num_pages": num_pages,
                "corrected_text": rewrite,
                "thread_count": len(threads),
            }),
            status=200
        )

    def register_post_thread_response(self, thread_data):
        """Register a mock response for POST on the CS commentable endpoint"""
        httpretty.register_uri(
            httpretty.POST,
            re.compile(r"http://localhost:4567/api/v1/(\w+)/threads"),
            body=_get_thread_callback(thread_data)
        )

    def register_put_thread_response(self, thread_data):
        """
        Register a mock response for PUT on the CS endpoint for the given
        thread_id.
        """
        httpretty.register_uri(
            httpretty.PUT,
            "http://localhost:4567/api/v1/threads/{}".format(thread_data["id"]),
            body=_get_thread_callback(thread_data)
        )

    def register_get_thread_error_response(self, thread_id, status_code):
        """Register a mock error response for GET on the CS thread endpoint."""
        httpretty.register_uri(
            httpretty.GET,
            "http://localhost:4567/api/v1/threads/{id}".format(id=thread_id),
            body="",
            status=status_code
        )

    def register_get_thread_response(self, thread):
        """
        Register a mock response for GET on the CS thread instance endpoint.
        """
        httpretty.register_uri(
            httpretty.GET,
            "http://localhost:4567/api/v1/threads/{id}".format(id=thread["id"]),
            body=json.dumps(thread),
            status=200
        )

    def register_post_comment_response(self, comment_data, thread_id, parent_id=None):
        """
        Register a mock response for POST on the CS comments endpoint for the
        given thread or parent; exactly one of thread_id and parent_id must be
        specified.
        """
        if parent_id:
            url = "http://localhost:4567/api/v1/comments/{}".format(parent_id)
        else:
            url = "http://localhost:4567/api/v1/threads/{}/comments".format(thread_id)

        httpretty.register_uri(
            httpretty.POST,
            url,
            body=_get_comment_callback(comment_data, thread_id, parent_id)
        )

    def register_put_comment_response(self, comment_data):
        """
        Register a mock response for PUT on the CS endpoint for the given
        comment data (which must include the key "id").
        """
        thread_id = comment_data["thread_id"]
        parent_id = comment_data.get("parent_id")
        httpretty.register_uri(
            httpretty.PUT,
            "http://localhost:4567/api/v1/comments/{}".format(comment_data["id"]),
            body=_get_comment_callback(comment_data, thread_id, parent_id)
        )

    def register_get_comment_error_response(self, comment_id, status_code):
        """
        Register a mock error response for GET on the CS comment instance
        endpoint.
        """
        httpretty.register_uri(
            httpretty.GET,
            "http://localhost:4567/api/v1/comments/{id}".format(id=comment_id),
            body="",
            status=status_code
        )

    def register_get_comment_response(self, response_overrides):
        """
        Register a mock response for GET on the CS comment instance endpoint.
        """
        comment = make_minimal_cs_comment(response_overrides)
        httpretty.register_uri(
            httpretty.GET,
            "http://localhost:4567/api/v1/comments/{id}".format(id=comment["id"]),
            body=json.dumps(comment),
            status=200
        )

    def register_get_user_response(self, user, subscribed_thread_ids=None, upvoted_ids=None):
        """Register a mock response for GET on the CS user instance endpoint"""
        httpretty.register_uri(
            httpretty.GET,
            "http://localhost:4567/api/v1/users/{id}".format(id=user.id),
            body=json.dumps({
                "id": str(user.id),
                "subscribed_thread_ids": subscribed_thread_ids or [],
                "upvoted_ids": upvoted_ids or [],
            }),
            status=200
        )

    def register_subscribed_threads_response(self, user, threads, page, num_pages):
        """Register a mock response for GET on the CS user instance endpoint"""
        httpretty.register_uri(
            httpretty.GET,
            "http://localhost:4567/api/v1/users/{}/subscribed_threads".format(user.id),
            body=json.dumps({
                "collection": threads,
                "page": page,
                "num_pages": num_pages,
                "thread_count": len(threads),
            }),
            status=200
        )

    def register_subscription_response(self, user):
        """
        Register a mock response for POST and DELETE on the CS user subscription
        endpoint
        """
        for method in [httpretty.POST, httpretty.DELETE]:
            httpretty.register_uri(
                method,
                "http://localhost:4567/api/v1/users/{id}/subscriptions".format(id=user.id),
                body=json.dumps({}),  # body is unused
                status=200
            )

    def register_thread_votes_response(self, thread_id):
        """
        Register a mock response for PUT and DELETE on the CS thread votes
        endpoint
        """
        for method in [httpretty.PUT, httpretty.DELETE]:
            httpretty.register_uri(
                method,
                "http://localhost:4567/api/v1/threads/{}/votes".format(thread_id),
                body=json.dumps({}),  # body is unused
                status=200
            )

    def register_comment_votes_response(self, comment_id):
        """
        Register a mock response for PUT and DELETE on the CS comment votes
        endpoint
        """
        for method in [httpretty.PUT, httpretty.DELETE]:
            httpretty.register_uri(
                method,
                "http://localhost:4567/api/v1/comments/{}/votes".format(comment_id),
                body=json.dumps({}),  # body is unused
                status=200
            )

    def register_flag_response(self, content_type, content_id):
        """Register a mock response for PUT on the CS flag endpoints"""
        for path in ["abuse_flag", "abuse_unflag"]:
            httpretty.register_uri(
                "PUT",
                "http://localhost:4567/api/v1/{content_type}s/{content_id}/{path}".format(
                    content_type=content_type,
                    content_id=content_id,
                    path=path
                ),
                body=json.dumps({}),  # body is unused
                status=200
            )

    def register_read_response(self, user, content_type, content_id):
        """
        Register a mock response for POST on the CS 'read' endpoint
        """
        httpretty.register_uri(
            httpretty.POST,
            "http://localhost:4567/api/v1/users/{id}/read".format(id=user.id),
            params={'source_type': content_type, 'source_id': content_id},
            body=json.dumps({}),  # body is unused
            status=200
        )

    def register_thread_flag_response(self, thread_id):
        """Register a mock response for PUT on the CS thread flag endpoints"""
        self.register_flag_response("thread", thread_id)

    def register_comment_flag_response(self, comment_id):
        """Register a mock response for PUT on the CS comment flag endpoints"""
        self.register_flag_response("comment", comment_id)

    def register_delete_thread_response(self, thread_id):
        """
        Register a mock response for DELETE on the CS thread instance endpoint
        """
        httpretty.register_uri(
            httpretty.DELETE,
            "http://localhost:4567/api/v1/threads/{id}".format(id=thread_id),
            body=json.dumps({}),  # body is unused
            status=200
        )

    def register_delete_comment_response(self, comment_id):
        """
        Register a mock response for DELETE on the CS comment instance endpoint
        """
        httpretty.register_uri(
            httpretty.DELETE,
            "http://localhost:4567/api/v1/comments/{id}".format(id=comment_id),
            body=json.dumps({}),  # body is unused
            status=200
        )

    def assert_query_params_equal(self, httpretty_request, expected_params):
        """
        Assert that the given mock request had the expected query parameters
        """
        actual_params = dict(httpretty_request.querystring)
        actual_params.pop("request_id")  # request_id is random
        self.assertEqual(actual_params, expected_params)

    def assert_last_query_params(self, expected_params):
        """
        Assert that the last mock request had the expected query parameters
        """
        self.assert_query_params_equal(httpretty.last_request(), expected_params)

    def request_patch(self, request_data):
        """
        make a request to PATCH endpoint and return response
        """
        return self.client.patch(
            self.url,
            json.dumps(request_data),
            content_type="application/merge-patch+json"
        )

    def expected_thread_data(self, overrides=None):
        """
        Returns expected thread data in API response
        """
        response_data = {
            "author": self.user.username,
            "author_label": None,
            "created_at": "1970-01-01T00:00:00Z",
            "updated_at": "1970-01-01T00:00:00Z",
            "raw_body": "Test body",
            "rendered_body": "<p>Test body</p>",
            "abuse_flagged": False,
            "voted": False,
            "vote_count": 0,
            "editable_fields": ["abuse_flagged", "following", "raw_body", "read", "title", "topic_id", "type", "voted"],
            "course_id": unicode(self.course.id),
            "topic_id": "test_topic",
            "group_id": None,
            "group_name": None,
            "title": "Test Title",
            "pinned": False,
            "closed": False,
            "following": False,
            "comment_count": 1,
            "unread_comment_count": 0,
            "comment_list_url": "http://testserver/api/discussion/v1/comments/?thread_id=test_thread",
            "endorsed_comment_list_url": None,
            "non_endorsed_comment_list_url": None,
            "read": False,
            "has_endorsed": False,
            "id": "test_thread",
            "type": "discussion",
            "response_count": 0,
        }
        response_data.update(overrides or {})
        return response_data


def make_minimal_cs_thread(overrides=None):
    """
    Create a dictionary containing all needed thread fields as returned by the
    comments service with dummy data and optional overrides
    """
    ret = {
        "type": "thread",
        "id": "dummy",
        "course_id": "dummy/dummy/dummy",
        "commentable_id": "dummy",
        "group_id": None,
        "user_id": "0",
        "username": "dummy",
        "anonymous": False,
        "anonymous_to_peers": False,
        "created_at": "1970-01-01T00:00:00Z",
        "updated_at": "1970-01-01T00:00:00Z",
        "last_activity_at": "1970-01-01T00:00:00Z",
        "thread_type": "discussion",
        "title": "dummy",
        "body": "dummy",
        "pinned": False,
        "closed": False,
        "abuse_flaggers": [],
        "votes": {"up_count": 0},
        "comments_count": 0,
        "unread_comments_count": 0,
        "children": [],
        "read": False,
        "endorsed": False,
        "resp_total": 0,
    }
    ret.update(overrides or {})
    return ret


def make_minimal_cs_comment(overrides=None):
    """
    Create a dictionary containing all needed comment fields as returned by the
    comments service with dummy data and optional overrides
    """
    ret = {
        "type": "comment",
        "id": "dummy",
        "commentable_id": "dummy",
        "thread_id": "dummy",
        "parent_id": None,
        "user_id": "0",
        "username": "dummy",
        "anonymous": False,
        "anonymous_to_peers": False,
        "created_at": "1970-01-01T00:00:00Z",
        "updated_at": "1970-01-01T00:00:00Z",
        "body": "dummy",
        "abuse_flaggers": [],
        "votes": {"up_count": 0},
        "endorsed": False,
        "child_count": 0,
        "children": [],
    }
    ret.update(overrides or {})
    return ret


def make_paginated_api_response(results=None, count=0, num_pages=0, next_link=None, previous_link=None):
    """
    Generates the response dictionary of paginated APIs with passed data
    """
    return {
        "pagination": {
            "next": next_link,
            "previous": previous_link,
            "count": count,
            "num_pages": num_pages,
        },
        "results": results or []
    }


class ProfileImageTestMixin(object):
    """
    Mixin with utility methods for user profile image
    """

    TEST_PROFILE_IMAGE_UPLOADED_AT = datetime(2002, 1, 9, 15, 43, 01, tzinfo=UTC)

    def create_profile_image(self, user, storage):
        """
        Creates profile image for user and checks that created image exists in storage
        """
        with make_image_file() as image_file:
            create_profile_images(image_file, get_profile_image_names(user.username))
            self.check_images(user, storage)
            set_has_profile_image(user.username, True, self.TEST_PROFILE_IMAGE_UPLOADED_AT)

    def check_images(self, user, storage, exist=True):
        """
        If exist is True, make sure the images physically exist in storage
        with correct sizes and formats.

        If exist is False, make sure none of the images exist.
        """
        for size, name in get_profile_image_names(user.username).items():
            if exist:
                self.assertTrue(storage.exists(name))
                with closing(Image.open(storage.path(name))) as img:
                    self.assertEqual(img.size, (size, size))
                    self.assertEqual(img.format, 'JPEG')
            else:
                self.assertFalse(storage.exists(name))

    def get_expected_user_profile(self, username):
        """
        Returns the expected user profile data for a given username
        """
        url = 'http://example-storage.com/profile-images/{filename}_{{size}}.jpg?v={timestamp}'.format(
            filename=hashlib.md5('secret' + username).hexdigest(),
            timestamp=self.TEST_PROFILE_IMAGE_UPLOADED_AT.strftime("%s")
        )
        return {
            'profile': {
                'image': {
                    'has_image': True,
                    'image_url_full': url.format(size=500),
                    'image_url_large': url.format(size=120),
                    'image_url_medium': url.format(size=50),
                    'image_url_small': url.format(size=30),
                }
            }
        }
