"""
Discussion API test utilities
"""


import hashlib
import json
import re
from contextlib import closing
from datetime import datetime
from urllib.parse import parse_qs

import httpretty
from PIL import Image
from pytz import UTC

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
        original_data = response_data.copy()
        for key, val_list in parsed_body(request).items():
            val = val_list[0]
            if key in ["anonymous", "anonymous_to_peers", "closed", "pinned"]:
                response_data[key] = val == "True"
            elif key == "edit_reason_code":
                response_data["edit_history"] = [
                    {
                        "original_body": original_data["body"],
                        "author": thread_data.get('username'),
                        "reason_code": val,
                    },
                ]
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
        original_data = response_data.copy()
        # thread_id and parent_id are not included in request payload but
        # are returned by the comments service
        response_data["thread_id"] = thread_id
        response_data["parent_id"] = parent_id
        for key, val_list in parsed_body(request).items():
            val = val_list[0]
            if key in ["anonymous", "anonymous_to_peers", "endorsed"]:
                response_data[key] = val == "True"
            elif key == "edit_reason_code":
                response_data["edit_history"] = [
                    {
                        "original_body": original_data["body"],
                        "author": comment_data.get('username'),
                        "reason_code": val,
                    },
                ]
            else:
                response_data[key] = val
        return (200, headers, json.dumps(response_data))

    return callback


class CommentsServiceMockMixin:
    """Mixin with utility methods for mocking the comments service"""
    def register_get_threads_response(self, threads, page, num_pages):
        """Register a mock response for GET on the CS thread list endpoint"""
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'

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

    def register_get_course_commentable_counts_response(self, course_id, thread_counts):
        """Register a mock response for GET on the CS thread list endpoint"""
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'

        httpretty.register_uri(
            httpretty.GET,
            f"http://localhost:4567/api/v1/commentables/{course_id}/counts",
            body=json.dumps(thread_counts),
            status=200
        )

    def register_get_threads_search_response(self, threads, rewrite, num_pages=1):
        """Register a mock response for GET on the CS thread search endpoint"""
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
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
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
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
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.PUT,
            "http://localhost:4567/api/v1/threads/{}".format(thread_data["id"]),
            body=_get_thread_callback(thread_data)
        )

    def register_get_thread_error_response(self, thread_id, status_code):
        """Register a mock error response for GET on the CS thread endpoint."""
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.GET,
            f"http://localhost:4567/api/v1/threads/{thread_id}",
            body="",
            status=status_code
        )

    def register_get_thread_response(self, thread):
        """
        Register a mock response for GET on the CS thread instance endpoint.
        """
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.GET,
            "http://localhost:4567/api/v1/threads/{id}".format(id=thread["id"]),
            body=json.dumps(thread),
            status=200
        )

    def register_get_comments_response(self, comments, page, num_pages):
        """Register a mock response for GET on the CS comments list endpoint"""
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'

        httpretty.register_uri(
            httpretty.GET,
            "http://localhost:4567/api/v1/comments",
            body=json.dumps({
                "collection": comments,
                "page": page,
                "num_pages": num_pages,
                "comment_count": len(comments),
            }),
            status=200
        )

    def register_post_comment_response(self, comment_data, thread_id, parent_id=None):
        """
        Register a mock response for POST on the CS comments endpoint for the
        given thread or parent; exactly one of thread_id and parent_id must be
        specified.
        """
        if parent_id:
            url = f"http://localhost:4567/api/v1/comments/{parent_id}"
        else:
            url = f"http://localhost:4567/api/v1/threads/{thread_id}/comments"

        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
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
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
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
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.GET,
            f"http://localhost:4567/api/v1/comments/{comment_id}",
            body="",
            status=status_code
        )

    def register_get_comment_response(self, response_overrides):
        """
        Register a mock response for GET on the CS comment instance endpoint.
        """
        comment = make_minimal_cs_comment(response_overrides)
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.GET,
            "http://localhost:4567/api/v1/comments/{id}".format(id=comment["id"]),
            body=json.dumps(comment),
            status=200
        )

    def register_get_user_response(self, user, subscribed_thread_ids=None, upvoted_ids=None):
        """Register a mock response for GET on the CS user instance endpoint"""
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.GET,
            f"http://localhost:4567/api/v1/users/{user.id}",
            body=json.dumps({
                "id": str(user.id),
                "subscribed_thread_ids": subscribed_thread_ids or [],
                "upvoted_ids": upvoted_ids or [],
            }),
            status=200
        )

    def register_get_user_retire_response(self, user, status=200, body=""):
        """Register a mock response for GET on the CS user retirement endpoint"""
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.POST,
            f"http://localhost:4567/api/v1/users/{user.id}/retire",
            body=body,
            status=status
        )

    def register_get_username_replacement_response(self, user, status=200, body=""):
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.POST,
            f"http://localhost:4567/api/v1/users/{user.id}/replace_username",
            body=body,
            status=status
        )

    def register_subscribed_threads_response(self, user, threads, page, num_pages):
        """Register a mock response for GET on the CS user instance endpoint"""
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.GET,
            f"http://localhost:4567/api/v1/users/{user.id}/subscribed_threads",
            body=json.dumps({
                "collection": threads,
                "page": page,
                "num_pages": num_pages,
                "thread_count": len(threads),
            }),
            status=200
        )

    def register_course_stats_response(self, course_key, stats, page, num_pages):
        """Register a mock response for GET on the CS user course stats instance endpoint"""
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.GET,
            f"http://localhost:4567/api/v1/users/{course_key}/stats",
            body=json.dumps({
                "user_stats": stats,
                "page": page,
                "num_pages": num_pages,
                "count": len(stats),
            }),
            status=200
        )

    def register_subscription_response(self, user):
        """
        Register a mock response for POST and DELETE on the CS user subscription
        endpoint
        """
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        for method in [httpretty.POST, httpretty.DELETE]:
            httpretty.register_uri(
                method,
                f"http://localhost:4567/api/v1/users/{user.id}/subscriptions",
                body=json.dumps({}),  # body is unused
                status=200
            )

    def register_thread_votes_response(self, thread_id):
        """
        Register a mock response for PUT and DELETE on the CS thread votes
        endpoint
        """
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        for method in [httpretty.PUT, httpretty.DELETE]:
            httpretty.register_uri(
                method,
                f"http://localhost:4567/api/v1/threads/{thread_id}/votes",
                body=json.dumps({}),  # body is unused
                status=200
            )

    def register_comment_votes_response(self, comment_id):
        """
        Register a mock response for PUT and DELETE on the CS comment votes
        endpoint
        """
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        for method in [httpretty.PUT, httpretty.DELETE]:
            httpretty.register_uri(
                method,
                f"http://localhost:4567/api/v1/comments/{comment_id}/votes",
                body=json.dumps({}),  # body is unused
                status=200
            )

    def register_flag_response(self, content_type, content_id):
        """Register a mock response for PUT on the CS flag endpoints"""
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
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
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.POST,
            f"http://localhost:4567/api/v1/users/{user.id}/read",
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
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.DELETE,
            f"http://localhost:4567/api/v1/threads/{thread_id}",
            body=json.dumps({}),  # body is unused
            status=200
        )

    def register_delete_comment_response(self, comment_id):
        """
        Register a mock response for DELETE on the CS comment instance endpoint
        """
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.DELETE,
            f"http://localhost:4567/api/v1/comments/{comment_id}",
            body=json.dumps({}),  # body is unused
            status=200
        )

    def register_user_active_threads(self, user_id, response):
        """
        Register a mock response for GET on the CS comment active threads endpoint
        """
        assert httpretty.is_enabled(), 'httpretty must be enabled to mock calls.'
        httpretty.register_uri(
            httpretty.GET,
            f"http://localhost:4567/api/v1/users/{user_id}/active_threads",
            body=json.dumps(response),
            status=200
        )

    def assert_query_params_equal(self, httpretty_request, expected_params):
        """
        Assert that the given mock request had the expected query parameters
        """
        actual_params = dict(querystring(httpretty_request))
        actual_params.pop("request_id")  # request_id is random
        assert actual_params == expected_params

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
            "anonymous": False,
            "anonymous_to_peers": False,
            "author": self.user.username,
            "author_label": None,
            "created_at": "1970-01-01T00:00:00Z",
            "updated_at": "1970-01-01T00:00:00Z",
            "raw_body": "Test body",
            "rendered_body": "<p>Test body</p>",
            "preview_body": "Test body",
            "abuse_flagged": False,
            "abuse_flagged_count": None,
            "voted": False,
            "vote_count": 0,
            "editable_fields": [
                "abuse_flagged",
                "anonymous",
                "copy_link",
                "following",
                "raw_body",
                "read",
                "title",
                "topic_id",
                "type",
                "voted",
            ],
            "course_id": str(self.course.id),
            "topic_id": "test_topic",
            "group_id": None,
            "group_name": None,
            "title": "Test Title",
            "pinned": False,
            "closed": False,
            "can_delete": True,
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
            "last_edit": None,
            "closed_by": None,
            "close_reason": None,
            "close_reason_code": None,
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
        "course_id": "course-v1:dummy+dummy+dummy",
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
        "abuse_flagged_count": None,
        "votes": {"up_count": 0},
        "comments_count": 0,
        "unread_comments_count": 0,
        "children": [],
        "read": False,
        "endorsed": False,
        "resp_total": 0,
        "closed_by": None,
        "close_reason_code": None,
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


class ProfileImageTestMixin:
    """
    Mixin with utility methods for user profile image
    """

    TEST_PROFILE_IMAGE_UPLOADED_AT = datetime(2002, 1, 9, 15, 43, 1, tzinfo=UTC)

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
                assert storage.exists(name)
                with closing(Image.open(storage.path(name))) as img:
                    assert img.size == (size, size)
                    assert img.format == 'JPEG'
            else:
                assert not storage.exists(name)

    def get_expected_user_profile(self, username):
        """
        Returns the expected user profile data for a given username
        """
        url = 'http://example-storage.com/profile-images/{filename}_{{size}}.jpg?v={timestamp}'.format(
            filename=hashlib.md5(b'secret' + username.encode('utf-8')).hexdigest(),
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


def parsed_body(request):
    """Returns a parsed dictionary version of a request body"""
    # This could just be HTTPrettyRequest.parsed_body, but that method double-decodes '%2B' -> '+' -> ' '.
    # You can just remove this method when this issue is fixed: https://github.com/gabrielfalcao/HTTPretty/issues/240
    return parse_qs(request.body.decode('utf8'))


def querystring(request):
    """Returns a parsed dictionary version of a query string"""
    # This could just be HTTPrettyRequest.querystring, but that method double-decodes '%2B' -> '+' -> ' '.
    # You can just remove this method when this issue is fixed: https://github.com/gabrielfalcao/HTTPretty/issues/240
    return parse_qs(request.path.split('?', 1)[-1])
