# pylint: skip-file
"""
Tests for the external REST API endpoints of the Discussion API (views_v2.py).

This module focuses on integration tests for the Django REST Framework views that expose the Discussion API.
It verifies the correct behavior of the API endpoints, including authentication, permissions, request/response formats,
and integration with the underlying discussion service. These tests ensure that the endpoints correctly handle
various user roles, input data, and edge cases, and that they return appropriate HTTP status codes and response bodies.
"""


import json
import random
from datetime import datetime
from unittest import mock
from urllib.parse import parse_qs, urlencode, urlparse

import ddt
import httpretty
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag
from lms.djangoapps.discussion.django_comment_client.tests.mixins import MockForumApiMixin
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.test import APIClient, APITestCase

from lms.djangoapps.discussion.toggles import ENABLE_DISCUSSIONS_MFE
from lms.djangoapps.discussion.rest_api.utils import get_usernames_from_search_string
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory, check_mongo_calls

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.models import get_retired_username_by_username, CourseEnrollment
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole, GlobalStaff
from common.djangoapps.student.tests.factories import (
    AdminFactory,
    CourseEnrollmentFactory,
    SuperuserFactory,
    UserFactory
)
from common.djangoapps.util.testing import PatchMediaTypeMixin, UrlResetMixin
from common.test.utils import disable_signal
from lms.djangoapps.discussion.tests.utils import (
    make_minimal_cs_comment,
    make_minimal_cs_thread,
)
from lms.djangoapps.discussion.django_comment_client.tests.utils import (
    ForumsEnableMixin,
    config_course_discussions,
    topic_name_to_id,
)
from lms.djangoapps.discussion.rest_api import api
from lms.djangoapps.discussion.rest_api.tests.utils import (
    CommentsServiceMockMixin,
    ForumMockUtilsMixin,
    ProfileImageTestMixin,
    make_paginated_api_response,
    parsed_body,
)
from openedx.core.djangoapps.course_groups.tests.helpers import config_course_cohorts
from openedx.core.djangoapps.discussions.config.waffle import ENABLE_NEW_STRUCTURE_DISCUSSIONS
from openedx.core.djangoapps.discussions.models import DiscussionsConfiguration, DiscussionTopicLink, Provider
from openedx.core.djangoapps.discussions.tasks import update_discussions_settings_from_course_task
from openedx.core.djangoapps.django_comment_common.models import CourseDiscussionSettings, Role
from openedx.core.djangoapps.django_comment_common.utils import seed_permissions_roles
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.djangoapps.oauth_dispatch.tests.factories import AccessTokenFactory, ApplicationFactory
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_storage
from openedx.core.djangoapps.user_api.models import RetirementState, UserRetirementStatus


class DiscussionAPIViewTestMixin(ForumsEnableMixin, ForumMockUtilsMixin, UrlResetMixin):
    """
    Mixin for common code in tests of Discussion API views. This includes
    creation of common structures (e.g. a course, user, and enrollment), logging
    in the test client, utility functions, and a test case for unauthenticated
    requests. Subclasses must set self.url in their setUp methods.
    """

    client_class = APIClient

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()
        self.maxDiff = None  # pylint: disable=invalid-name
        self.course = CourseFactory.create(
            org="x",
            course="y",
            run="z",
            start=datetime.now(UTC),
            discussion_topics={"Test Topic": {"id": "test_topic"}}
        )
        self.password = "Password1234"
        self.user = UserFactory.create(password=self.password)
        # Ensure that parental controls don't apply to this user
        self.user.profile.year_of_birth = 1970
        self.user.profile.save()
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.client.login(username=self.user.username, password=self.password)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        super().disposeForumMocks()

    def assert_response_correct(self, response, expected_status, expected_content):
        """
        Assert that the response has the given status code and parsed content
        """
        assert response.status_code == expected_status
        parsed_content = json.loads(response.content.decode('utf-8'))
        assert parsed_content == expected_content

    def register_thread(self, overrides=None):
        """
        Create cs_thread with minimal fields and register response
        """
        cs_thread = make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": str(self.course.id),
            "commentable_id": "test_topic",
            "username": self.user.username,
            "user_id": str(self.user.id),
            "thread_type": "discussion",
            "title": "Test Title",
            "body": "Test body",
        })
        cs_thread.update(overrides or {})
        self.register_get_thread_response(cs_thread)
        self.register_put_thread_response(cs_thread)

    def register_comment(self, overrides=None):
        """
        Create cs_comment with minimal fields and register response
        """
        cs_comment = make_minimal_cs_comment({
            "id": "test_comment",
            "course_id": str(self.course.id),
            "thread_id": "test_thread",
            "username": self.user.username,
            "user_id": str(self.user.id),
            "body": "Original body",
        })
        cs_comment.update(overrides or {})
        self.register_get_comment_response(cs_comment)
        self.register_put_comment_response(cs_comment)
        self.register_post_comment_response(cs_comment, thread_id="test_thread")

    def test_not_authenticated(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assert_response_correct(
            response,
            401,
            {"developer_message": "Authentication credentials were not provided."}
        )

    def test_inactive(self):
        self.user.is_active = False
        self.test_basic()


@ddt.ddt
@httpretty.activate
@disable_signal(api, 'thread_edited')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class ThreadViewSetPartialUpdateTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase, PatchMediaTypeMixin):
    """Tests for ThreadViewSet partial_update"""

    def setUp(self):
        self.unsupported_media_type = JSONParser.media_type
        super().setUp()
        self.url = reverse("thread-detail", kwargs={"thread_id": "test_thread"})

    def test_basic(self):
        self.register_get_user_response(self.user)
        self.register_thread({
            "created_at": "Test Created Date",
            "updated_at": "Test Updated Date",
            "read": True,
            "resp_total": 2,
        })
        request_data = {"raw_body": "Edited body"}
        response = self.request_patch(request_data)
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data == self.expected_thread_data({
            'raw_body': 'Edited body',
            'rendered_body': '<p>Edited body</p>',
            'preview_body': 'Edited body',
            'editable_fields': [
                'abuse_flagged', 'anonymous', 'copy_link', 'following', 'raw_body', 'read',
                'title', 'topic_id', 'type'
            ],
            'created_at': 'Test Created Date',
            'updated_at': 'Test Updated Date',
            'comment_count': 1,
            'read': True,
            'response_count': 2,
        })

        params = {
            'thread_id': 'test_thread',
            'course_id': str(self.course.id),
            'commentable_id': 'test_topic',
            'thread_type': 'discussion',
            'title': 'Test Title',
            'body': 'Edited body',
            'user_id': str(self.user.id),
            'anonymous': False,
            'anonymous_to_peers': False,
            'closed': False,
            'pinned': False,
            'read': True,
            'editing_user_id': str(self.user.id),
        }
        self.check_mock_called_with('update_thread', -1, **params)

    def test_error(self):
        self.register_get_user_response(self.user)
        self.register_thread()
        request_data = {"title": ""}
        response = self.request_patch(request_data)
        expected_response_data = {
            "field_errors": {"title": {"developer_message": "This field may not be blank."}}
        }
        assert response.status_code == 400
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data == expected_response_data

    @ddt.data(
        ("abuse_flagged", True),
        ("abuse_flagged", False),
    )
    @ddt.unpack
    def test_closed_thread(self, field, value):
        self.register_get_user_response(self.user)
        self.register_thread({"closed": True, "read": True})
        self.register_flag_response("thread", "test_thread")
        request_data = {field: value}
        response = self.request_patch(request_data)
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data == self.expected_thread_data({
            'read': True,
            'closed': True,
            'abuse_flagged': value,
            'editable_fields': ['abuse_flagged', 'copy_link', 'read'],
            'comment_count': 1, 'unread_comment_count': 0
        })

    @ddt.data(
        ("raw_body", "Edited body"),
        ("voted", True),
        ("following", True),
    )
    @ddt.unpack
    def test_closed_thread_error(self, field, value):
        self.register_get_user_response(self.user)
        self.register_thread({"closed": True})
        self.register_flag_response("thread", "test_thread")
        request_data = {field: value}
        response = self.request_patch(request_data)
        assert response.status_code == 400

    def test_patch_read_owner_user(self):
        self.register_get_user_response(self.user)
        self.register_thread({"resp_total": 2})
        self.register_read_response(self.user, "thread", "test_thread")
        request_data = {"read": True}

        response = self.request_patch(request_data)
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data == self.expected_thread_data({
            'comment_count': 1,
            'read': True,
            'editable_fields': [
                'abuse_flagged', 'anonymous', 'copy_link', 'following', 'raw_body', 'read',
                'title', 'topic_id', 'type'
            ],
            'response_count': 2
        })

    def test_patch_read_non_owner_user(self):
        self.register_get_user_response(self.user)
        thread_owner_user = UserFactory.create(password=self.password)
        CourseEnrollmentFactory.create(user=thread_owner_user, course_id=self.course.id)
        self.register_thread({
            "username": thread_owner_user.username,
            "user_id": str(thread_owner_user.id),
            "resp_total": 2,
        })
        self.register_read_response(self.user, "thread", "test_thread")

        request_data = {"read": True}
        response = self.request_patch(request_data)
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        expected_data = self.expected_thread_data({
            'author': str(thread_owner_user.username),
            'comment_count': 1,
            'can_delete': False,
            'read': True,
            'editable_fields': ['abuse_flagged', 'copy_link', 'following', 'read', 'voted'],
            'response_count': 2
        })
        assert response_data == expected_data


@ddt.ddt
@disable_signal(api, 'comment_edited')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CommentViewSetPartialUpdateTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase, PatchMediaTypeMixin):
    """Tests for CommentViewSet partial_update"""

    def setUp(self):
        self.unsupported_media_type = JSONParser.media_type
        super().setUp()
        self.register_get_user_response(self.user)
        self.url = reverse("comment-detail", kwargs={"comment_id": "test_comment"})

    def expected_response_data(self, overrides=None):
        """
        create expected response data from comment update endpoint
        """
        response_data = {
            "id": "test_comment",
            "thread_id": "test_thread",
            "parent_id": None,
            "author": self.user.username,
            "author_label": None,
            "created_at": "1970-01-01T00:00:00Z",
            "updated_at": "1970-01-01T00:00:00Z",
            "raw_body": "Original body",
            "rendered_body": "<p>Original body</p>",
            "endorsed": False,
            "endorsed_by": None,
            "endorsed_by_label": None,
            "endorsed_at": None,
            "abuse_flagged": False,
            "abuse_flagged_any_user": None,
            "voted": False,
            "vote_count": 0,
            "children": [],
            "editable_fields": [],
            "child_count": 0,
            "can_delete": True,
            "anonymous": False,
            "anonymous_to_peers": False,
            "last_edit": None,
            "edit_by_label": None,
            "profile_image": {
                "has_image": False,
                "image_url_full": "http://testserver/static/default_500.png",
                "image_url_large": "http://testserver/static/default_120.png",
                "image_url_medium": "http://testserver/static/default_50.png",
                "image_url_small": "http://testserver/static/default_30.png",
            },
        }
        response_data.update(overrides or {})
        return response_data

    def test_basic(self):
        self.register_thread()
        self.register_comment({"created_at": "Test Created Date", "updated_at": "Test Updated Date"})
        request_data = {"raw_body": "Edited body"}
        response = self.request_patch(request_data)
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data == self.expected_response_data({
            'raw_body': 'Edited body',
            'rendered_body': '<p>Edited body</p>',
            'editable_fields': ['abuse_flagged', 'anonymous', 'raw_body'],
            'created_at': 'Test Created Date',
            'updated_at': 'Test Updated Date'
        })
        params = {
            'comment_id': 'test_comment',
            'body': 'Edited body',
            'course_id': str(self.course.id),
            'user_id': str(self.user.id),
            'anonymous': False,
            'anonymous_to_peers': False,
            'endorsed': False,
            'editing_user_id': str(self.user.id),
        }
        self.check_mock_called_with('update_comment', -1, **params)

    def test_error(self):
        self.register_thread()
        self.register_comment()
        request_data = {"raw_body": ""}
        response = self.request_patch(request_data)
        expected_response_data = {
            "field_errors": {"raw_body": {"developer_message": "This field may not be blank."}}
        }
        assert response.status_code == 400
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data == expected_response_data

    @ddt.data(
        ("abuse_flagged", True),
        ("abuse_flagged", False),
    )
    @ddt.unpack
    def test_closed_thread(self, field, value):
        self.register_thread({"closed": True})
        self.register_comment()
        self.register_flag_response("comment", "test_comment")
        request_data = {field: value}
        response = self.request_patch(request_data)
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data == self.expected_response_data({
            'abuse_flagged': value,
            "abuse_flagged_any_user": None,
            'editable_fields': ['abuse_flagged']
        })

    @ddt.data(
        ("raw_body", "Edited body"),
        ("voted", True),
        ("following", True),
    )
    @ddt.unpack
    def test_closed_thread_error(self, field, value):
        self.register_thread({"closed": True})
        self.register_comment()
        request_data = {field: value}
        response = self.request_patch(request_data)
        assert response.status_code == 400
