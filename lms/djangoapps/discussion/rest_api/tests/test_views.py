"""
Tests for Discussion API views
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
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.test import APIClient, APITestCase

from lms.djangoapps.discussion.config.waffle import ENABLE_LEARNERS_STATS
from lms.djangoapps.discussion.rest_api.utils import get_usernames_from_search_string
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.models import get_retired_username_by_username, CourseEnrollment
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole, GlobalStaff
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, SuperuserFactory, UserFactory
from common.djangoapps.util.testing import PatchMediaTypeMixin, UrlResetMixin
from common.test.utils import disable_signal
from lms.djangoapps.discussion.django_comment_client.tests.utils import (
    ForumsEnableMixin,
    config_course_discussions,
    topic_name_to_id,
)
from lms.djangoapps.discussion.rest_api import api
from lms.djangoapps.discussion.rest_api.tests.utils import (
    CommentsServiceMockMixin,
    ProfileImageTestMixin,
    make_minimal_cs_comment,
    make_minimal_cs_thread,
    make_paginated_api_response,
    parsed_body,
)
from openedx.core.djangoapps.course_groups.tests.helpers import config_course_cohorts
from openedx.core.djangoapps.django_comment_common.models import CourseDiscussionSettings, Role
from openedx.core.djangoapps.django_comment_common.utils import seed_permissions_roles
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.djangoapps.oauth_dispatch.tests.factories import AccessTokenFactory, ApplicationFactory
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_storage
from openedx.core.djangoapps.user_api.models import RetirementState, UserRetirementStatus


class DiscussionAPIViewTestMixin(ForumsEnableMixin, CommentsServiceMockMixin, UrlResetMixin):
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
        self.password = "password"
        self.user = UserFactory.create(password=self.password)
        # Ensure that parental controls don't apply to this user
        self.user.profile.year_of_birth = 1970
        self.user.profile.save()
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.client.login(username=self.user.username, password=self.password)

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


@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class UploadFileViewTest(ForumsEnableMixin, CommentsServiceMockMixin, UrlResetMixin, ModuleStoreTestCase):
    """
    Tests for UploadFileView.
    """

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()
        self.valid_file = {
            "uploaded_file": SimpleUploadedFile(
                "test.jpg",
                b"test content",
                content_type="image/jpeg",
            ),
        }
        self.user = UserFactory.create(password="password")
        self.course = CourseFactory.create(org='a', course='b', run='c', start=datetime.now(UTC))
        self.url = reverse("upload_file", kwargs={"course_id": str(self.course.id)})

    def user_login(self):
        """
        Authenticates the test client with the example user.
        """
        self.client.login(username=self.user.username, password="password")

    def enroll_user_in_course(self):
        """
        Makes the example user enrolled to the course.
        """
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

    def assert_upload_success(self, response):
        """
        Asserts that the upload response was successful and returned the
        expected contents.
        """
        assert response.status_code == status.HTTP_200_OK
        assert response.content_type == "application/json"
        response_data = json.loads(response.content)
        assert "location" in response_data

    def test_file_upload_by_unauthenticated_user(self):
        """
        Should fail if an unauthenticated user tries to upload a file.
        """
        response = self.client.post(self.url, self.valid_file)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_file_upload_by_unauthorized_user(self):
        """
        Should fail if the user is not either staff or a student
        enrolled in the course.
        """
        self.user_login()
        response = self.client.post(self.url, self.valid_file)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_file_upload_by_enrolled_user(self):
        """
        Should succeed when a valid file is uploaded by an authenticated
        user who's enrolled in the course.
        """
        self.user_login()
        self.enroll_user_in_course()
        response = self.client.post(self.url, self.valid_file)
        self.assert_upload_success(response)

    def test_file_upload_by_global_staff(self):
        """
        Should succeed when a valid file is uploaded by a global staff
        member.
        """
        self.user_login()
        GlobalStaff().add_users(self.user)
        response = self.client.post(self.url, self.valid_file)
        self.assert_upload_success(response)

    def test_file_upload_by_instructor(self):
        """
        Should succeed when a valid file is uploaded by a course instructor.
        """
        self.user_login()
        CourseInstructorRole(course_key=self.course.id).add_users(self.user)
        response = self.client.post(self.url, self.valid_file)
        self.assert_upload_success(response)

    def test_file_upload_by_course_staff(self):
        """
        Should succeed when a valid file is uploaded by a course staff
        member.
        """
        self.user_login()
        CourseStaffRole(course_key=self.course.id).add_users(self.user)
        response = self.client.post(self.url, self.valid_file)
        self.assert_upload_success(response)

    def test_file_upload_with_thread_key(self):
        """
        Should contain the given thread_key in the uploaded file name.
        """
        self.user_login()
        self.enroll_user_in_course()
        response = self.client.post(self.url, {
            **self.valid_file,
            "thread_key": "somethread",
        })
        response_data = json.loads(response.content)
        assert "/somethread/" in response_data["location"]

    def test_file_upload_with_invalid_file(self):
        """
        Should fail if the uploaded file format is not allowed.
        """
        self.user_login()
        self.enroll_user_in_course()
        invalid_file = {
            "uploaded_file": SimpleUploadedFile(
                "test.txt",
                b"test content",
                content_type="text/plain",
            ),
        }
        response = self.client.post(self.url, invalid_file)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_file_upload_with_invalid_course_id(self):
        """
        Should fail if the course does not exist.
        """
        self.user_login()
        self.enroll_user_in_course()
        url = reverse("upload_file", kwargs={"course_id": "d/e/f"})
        response = self.client.post(url, self.valid_file)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_file_upload_with_no_data(self):
        """
        Should fail when the user sends a request missing an
        `uploaded_file` field.
        """
        self.user_login()
        self.enroll_user_in_course()
        response = self.client.post(self.url, data={})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@ddt.ddt
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CommentViewSetListByUserTest(
    ForumsEnableMixin,
    CommentsServiceMockMixin,
    UrlResetMixin,
    ModuleStoreTestCase,
):
    """
    Common test cases for views retrieving user-published content.
    """

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()

        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.reset)
        self.addCleanup(httpretty.disable)

        self.user = UserFactory.create(password="password")
        self.register_get_user_response(self.user)

        self.other_user = UserFactory.create(password="password")
        self.register_get_user_response(self.other_user)

        self.course = CourseFactory.create(org="a", course="b", run="c", start=datetime.now(UTC))
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

        self.url = self.build_url(self.user.username, self.course.id)

    def register_mock_endpoints(self):
        """
        Register cs_comments_service mocks for sample threads and comments.
        """
        self.register_get_threads_response(
            threads=[
                make_minimal_cs_thread({
                    "id": f"test_thread_{index}",
                    "course_id": str(self.course.id),
                    "commentable_id": f"test_topic_{index}",
                    "username": self.user.username,
                    "user_id": str(self.user.id),
                    "thread_type": "discussion",
                    "title": f"Test Title #{index}",
                    "body": f"Test body #{index}",
                })
                for index in range(30)
            ],
            page=1,
            num_pages=1,
        )
        self.register_get_comments_response(
            comments=[
                make_minimal_cs_comment({
                    "id": f"test_comment_{index}",
                    "thread_id": "test_thread",
                    "user_id": str(self.user.id),
                    "username": self.user.username,
                    "created_at": "2015-05-11T00:00:00Z",
                    "updated_at": "2015-05-11T11:11:11Z",
                    "body": f"Test body #{index}",
                    "votes": {"up_count": 4},
                })
                for index in range(30)
            ],
            page=1,
            num_pages=1,
        )

    def build_url(self, username, course_id, **kwargs):
        """
        Builds an URL to access content from an user on a specific course.
        """
        base = reverse("comment-list")
        query = urlencode({
            "username": username,
            "course_id": str(course_id),
            **kwargs,
        })
        return f"{base}?{query}"

    def assert_successful_response(self, response):
        """
        Check that the response was successful and contains the expected fields.
        """
        assert response.status_code == status.HTTP_200_OK
        response_data = json.loads(response.content)
        assert "results" in response_data
        assert "pagination" in response_data

    def test_request_by_unauthenticated_user(self):
        """
        Unauthenticated users are not allowed to request users content.
        """
        self.register_mock_endpoints()
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_request_by_unauthorized_user(self):
        """
        Users are not allowed to request content from courses in which
        they're not either enrolled or staff members.
        """
        self.register_mock_endpoints()
        self.client.login(username=self.other_user.username, password="password")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert json.loads(response.content)["developer_message"] == "Course not found."

    def test_request_by_enrolled_user(self):
        """
        Users that are enrolled in a course are allowed to get users'
        comments in that course.
        """
        self.register_mock_endpoints()
        self.client.login(username=self.other_user.username, password="password")
        CourseEnrollmentFactory.create(user=self.other_user, course_id=self.course.id)
        self.assert_successful_response(self.client.get(self.url))

    def test_request_by_global_staff(self):
        """
        Staff users are allowed to get any user's comments.
        """
        self.register_mock_endpoints()
        self.client.login(username=self.other_user.username, password="password")
        GlobalStaff().add_users(self.other_user)
        self.assert_successful_response(self.client.get(self.url))

    @ddt.data(CourseStaffRole, CourseInstructorRole)
    def test_request_by_course_staff(self, role):
        """
        Course staff users are allowed to get an user's comments in that
        course.
        """
        self.register_mock_endpoints()
        self.client.login(username=self.other_user.username, password="password")
        role(course_key=self.course.id).add_users(self.other_user)
        self.assert_successful_response(self.client.get(self.url))

    def test_request_with_non_existent_user(self):
        """
        Requests for users that don't exist result in a 404 response.
        """
        self.register_mock_endpoints()
        self.client.login(username=self.other_user.username, password="password")
        GlobalStaff().add_users(self.other_user)
        url = self.build_url("non_existent", self.course.id)
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_request_with_non_existent_course(self):
        """
        Requests for courses that don't exist result in a 404 response.
        """
        self.register_mock_endpoints()
        self.client.login(username=self.other_user.username, password="password")
        GlobalStaff().add_users(self.other_user)
        url = self.build_url(self.user.username, "course-v1:x+y+z")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_request_with_invalid_course_id(self):
        """
        Requests with invalid course ID should fail form validation.
        """
        self.register_mock_endpoints()
        self.client.login(username=self.other_user.username, password="password")
        GlobalStaff().add_users(self.other_user)
        url = self.build_url(self.user.username, "an invalid course")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        parsed_response = json.loads(response.content)
        assert parsed_response["field_errors"]["course_id"]["developer_message"] == \
            "'an invalid course' is not a valid course id"

    def test_request_with_empty_results_page(self):
        """
        Requests for pages that exceed the available number of pages
        result in a 404 response.
        """
        self.register_get_threads_response(threads=[], page=1, num_pages=1)
        self.register_get_comments_response(comments=[], page=1, num_pages=1)

        self.client.login(username=self.other_user.username, password="password")
        GlobalStaff().add_users(self.other_user)
        url = self.build_url(self.user.username, self.course.id, page=2)
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
@override_settings(DISCUSSION_MODERATION_EDIT_REASON_CODES={"test-edit-reason": "Test Edit Reason"})
@override_settings(DISCUSSION_MODERATION_CLOSE_REASON_CODES={"test-close-reason": "Test Close Reason"})
class CourseViewTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for CourseView"""
    def setUp(self):
        super().setUp()
        self.url = reverse("discussion_course", kwargs={"course_id": str(self.course.id)})

    def test_404(self):
        response = self.client.get(
            reverse("course_topics", kwargs={"course_id": "non/existent/course"})
        )
        self.assert_response_correct(
            response,
            404,
            {"developer_message": "Course not found."}
        )

    def test_basic(self):
        response = self.client.get(self.url)
        self.assert_response_correct(
            response,
            200,
            {
                "id": str(self.course.id),
                "blackouts": [],
                "thread_list_url": "http://testserver/api/discussion/v1/threads/?course_id=course-v1%3Ax%2By%2Bz",
                "following_thread_list_url": (
                    "http://testserver/api/discussion/v1/threads/?course_id=course-v1%3Ax%2By%2Bz&following=True"
                ),
                "topics_url": "http://testserver/api/discussion/v1/course_topics/course-v1:x+y+z",
                "enable_in_context": True,
                "group_at_subsection": False,
                "provider": "legacy",
                "allow_anonymous": True,
                "allow_anonymous_to_peers": False,
                "has_moderation_privileges": False,
                "is_group_ta": False,
                'is_user_admin': False,
                "user_roles": ["Student"],
                'learners_tab_enabled': False,
                "reason_codes_enabled": False,
                "edit_reasons": [{"code": "test-edit-reason", "label": "Test Edit Reason"}],
                "post_close_reasons": [{"code": "test-close-reason", "label": "Test Close Reason"}],
            }
        )


@httpretty.activate
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class RetireViewTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for CourseView"""
    def setUp(self):
        super().setUp()
        RetirementState.objects.create(state_name='PENDING', state_execution_order=1)
        self.retire_forums_state = RetirementState.objects.create(state_name='RETIRE_FORUMS', state_execution_order=11)

        self.retirement = UserRetirementStatus.create_retirement(self.user)
        self.retirement.current_state = self.retire_forums_state
        self.retirement.save()

        self.superuser = SuperuserFactory()
        self.superuser_client = APIClient()
        self.retired_username = get_retired_username_by_username(self.user.username)
        self.url = reverse("retire_discussion_user")

    def assert_response_correct(self, response, expected_status, expected_content):
        """
        Assert that the response has the given status code and content
        """
        assert response.status_code == expected_status

        if expected_content:
            assert response.content.decode('utf-8') == expected_content

    def build_jwt_headers(self, user):
        """
        Helper function for creating headers for the JWT authentication.
        """
        token = create_jwt_for_user(user)
        headers = {'HTTP_AUTHORIZATION': 'JWT ' + token}
        return headers

    def test_basic(self):
        """
        Check successful retirement case
        """
        self.register_get_user_retire_response(self.user)
        headers = self.build_jwt_headers(self.superuser)
        data = {'username': self.user.username}
        response = self.superuser_client.post(self.url, data, **headers)
        self.assert_response_correct(response, 204, b"")

    def test_downstream_forums_error(self):
        """
        Check that we bubble up errors from the comments service
        """
        self.register_get_user_retire_response(self.user, status=500, body="Server error")
        headers = self.build_jwt_headers(self.superuser)
        data = {'username': self.user.username}
        response = self.superuser_client.post(self.url, data, **headers)
        self.assert_response_correct(response, 500, '"Server error"')

    def test_nonexistent_user(self):
        """
        Check that we handle unknown users appropriately
        """
        nonexistent_username = "nonexistent user"
        self.retired_username = get_retired_username_by_username(nonexistent_username)
        data = {'username': nonexistent_username}
        headers = self.build_jwt_headers(self.superuser)
        response = self.superuser_client.post(self.url, data, **headers)
        self.assert_response_correct(response, 404, None)

    def test_not_authenticated(self):
        """
        Override the parent implementation of this, we JWT auth for this API
        """
        pass  # lint-amnesty, pylint: disable=unnecessary-pass


@ddt.ddt
@httpretty.activate
@mock.patch('django.conf.settings.USERNAME_REPLACEMENT_WORKER', 'test_replace_username_service_worker')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class ReplaceUsernamesViewTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for ReplaceUsernamesView"""
    def setUp(self):
        super().setUp()
        self.worker = UserFactory()
        self.worker.username = "test_replace_username_service_worker"
        self.worker_client = APIClient()
        self.new_username = "test_username_replacement"
        self.url = reverse("replace_discussion_username")

    def assert_response_correct(self, response, expected_status, expected_content):
        """
        Assert that the response has the given status code and content
        """
        assert response.status_code == expected_status

        if expected_content:
            assert str(response.content) == expected_content

    def build_jwt_headers(self, user):
        """
        Helper function for creating headers for the JWT authentication.
        """
        token = create_jwt_for_user(user)
        headers = {'HTTP_AUTHORIZATION': 'JWT ' + token}
        return headers

    def call_api(self, user, client, data):
        """ Helper function to call API with data """
        data = json.dumps(data)
        headers = self.build_jwt_headers(user)
        return client.post(self.url, data, content_type='application/json', **headers)

    @ddt.data(
        [{}, {}],
        {},
        [{"test_key": "test_value", "test_key_2": "test_value_2"}]
    )
    def test_bad_schema(self, mapping_data):
        """ Verify the endpoint rejects bad data schema """
        data = {
            "username_mappings": mapping_data
        }
        response = self.call_api(self.worker, self.worker_client, data)
        assert response.status_code == 400

    def test_auth(self):
        """ Verify the endpoint only works with the service worker """
        data = {
            "username_mappings": [
                {"test_username_1": "test_new_username_1"},
                {"test_username_2": "test_new_username_2"}
            ]
        }

        # Test unauthenticated
        response = self.client.post(self.url, data)
        assert response.status_code == 401

        # Test non-service worker
        random_user = UserFactory()
        response = self.call_api(random_user, APIClient(), data)
        assert response.status_code == 403

        # Test service worker
        response = self.call_api(self.worker, self.worker_client, data)
        assert response.status_code == 200

    def test_basic(self):
        """ Check successful replacement """
        data = {
            "username_mappings": [
                {self.user.username: self.new_username},
            ]
        }
        expected_response = {
            'failed_replacements': [],
            'successful_replacements': data["username_mappings"]
        }
        self.register_get_username_replacement_response(self.user)
        response = self.call_api(self.worker, self.worker_client, data)
        assert response.status_code == 200
        assert response.data == expected_response

    def test_not_authenticated(self):
        """
        Override the parent implementation of this, we JWT auth for this API
        """
        pass  # lint-amnesty, pylint: disable=unnecessary-pass


@ddt.ddt
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CourseTopicsViewTest(DiscussionAPIViewTestMixin, CommentsServiceMockMixin, ModuleStoreTestCase):
    """
    Tests for CourseTopicsView
    """
    def setUp(self):
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.reset)
        self.addCleanup(httpretty.disable)
        super().setUp()
        self.url = reverse("course_topics", kwargs={"course_id": str(self.course.id)})
        self.thread_counts_map = {
            "courseware-1": {"discussion": 2, "question": 3},
            "courseware-2": {"discussion": 4, "question": 5},
            "courseware-3": {"discussion": 7, "question": 2},
        }
        self.register_get_course_commentable_counts_response(self.course.id, self.thread_counts_map)

    def create_course(self, modules_count, module_store, topics):
        """
        Create a course in a specified module store with discussion xblocks and topics
        """
        course = CourseFactory.create(
            org="a",
            course="b",
            run="c",
            start=datetime.now(UTC),
            default_store=module_store,
            discussion_topics=topics
        )
        CourseEnrollmentFactory.create(user=self.user, course_id=course.id)
        course_url = reverse("course_topics", kwargs={"course_id": str(course.id)})
        # add some discussion xblocks
        for i in range(modules_count):
            ItemFactory.create(
                parent_location=course.location,
                category='discussion',
                discussion_id=f'id_module_{i}',
                discussion_category=f'Category {i}',
                discussion_target=f'Discussion {i}',
                publish_item=False,
            )
        return course_url, course.id

    def make_discussion_xblock(self, topic_id, category, subcategory, **kwargs):
        """
        Build a discussion xblock in self.course
        """
        ItemFactory.create(
            parent_location=self.course.location,
            category="discussion",
            discussion_id=topic_id,
            discussion_category=category,
            discussion_target=subcategory,
            **kwargs
        )

    def test_404(self):
        response = self.client.get(
            reverse("course_topics", kwargs={"course_id": "non/existent/course"})
        )
        self.assert_response_correct(
            response,
            404,
            {"developer_message": "Course not found."}
        )

    def test_basic(self):
        response = self.client.get(self.url)
        self.assert_response_correct(
            response,
            200,
            {
                "courseware_topics": [],
                "non_courseware_topics": [{
                    "id": "test_topic",
                    "name": "Test Topic",
                    "children": [],
                    "thread_list_url": 'http://testserver/api/discussion/v1/threads/'
                                       '?course_id=course-v1%3Ax%2By%2Bz&topic_id=test_topic',
                    "thread_counts": {"discussion": 0, "question": 0},
                }],
            }
        )

    @ddt.data(
        (2, ModuleStoreEnum.Type.split, 2, {"Test Topic 1": {"id": "test_topic_1"}}),
        (2, ModuleStoreEnum.Type.split, 2,
         {"Test Topic 1": {"id": "test_topic_1"}, "Test Topic 2": {"id": "test_topic_2"}}),
        (10, ModuleStoreEnum.Type.split, 2, {"Test Topic 1": {"id": "test_topic_1"}}),
    )
    @ddt.unpack
    def test_bulk_response(self, modules_count, module_store, mongo_calls, topics):
        course_url, course_id = self.create_course(modules_count, module_store, topics)
        self.register_get_course_commentable_counts_response(course_id, {})
        with check_mongo_calls(mongo_calls):
            with modulestore().default_store(module_store):
                self.client.get(course_url)

    def test_discussion_topic_404(self):
        """
        Tests discussion topic does not exist for the given topic id.
        """
        topic_id = "courseware-topic-id"
        self.make_discussion_xblock(topic_id, "test_category", "test_target")
        url = f"{self.url}?topic_id=invalid_topic_id"
        response = self.client.get(url)
        self.assert_response_correct(
            response,
            404,
            {"developer_message": "Discussion not found for 'invalid_topic_id'."}
        )

    def test_topic_id(self):
        """
        Tests discussion topic details against a requested topic id
        """
        topic_id_1 = "topic_id_1"
        topic_id_2 = "topic_id_2"
        self.make_discussion_xblock(topic_id_1, "test_category_1", "test_target_1")
        self.make_discussion_xblock(topic_id_2, "test_category_2", "test_target_2")
        url = f"{self.url}?topic_id=topic_id_1,topic_id_2"
        response = self.client.get(url)
        self.assert_response_correct(
            response,
            200,
            {
                "non_courseware_topics": [],
                "courseware_topics": [
                    {
                        "children": [{
                            "children": [],
                            "id": "topic_id_1",
                            "thread_list_url": "http://testserver/api/discussion/v1/threads/?"
                                               "course_id=course-v1%3Ax%2By%2Bz&topic_id=topic_id_1",
                            "name": "test_target_1",
                            "thread_counts": {"discussion": 0, "question": 0},
                        }],
                        "id": None,
                        "thread_list_url": "http://testserver/api/discussion/v1/threads/?"
                                           "course_id=course-v1%3Ax%2By%2Bz&topic_id=topic_id_1",
                        "name": "test_category_1",
                        "thread_counts": None,
                    },
                    {
                        "children":
                            [{
                                "children": [],
                                "id": "topic_id_2",
                                "thread_list_url": "http://testserver/api/discussion/v1/threads/?"
                                                   "course_id=course-v1%3Ax%2By%2Bz&topic_id=topic_id_2",
                                "name": "test_target_2",
                                "thread_counts": {"discussion": 0, "question": 0},
                            }],
                        "id": None,
                        "thread_list_url": "http://testserver/api/discussion/v1/threads/?"
                                           "course_id=course-v1%3Ax%2By%2Bz&topic_id=topic_id_2",
                        "name": "test_category_2",
                        "thread_counts": None,
                    }
                ]
            }
        )


@ddt.ddt
@httpretty.activate
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class ThreadViewSetListTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase, ProfileImageTestMixin):
    """Tests for ThreadViewSet list"""
    def setUp(self):
        super().setUp()
        self.author = UserFactory.create()
        self.url = reverse("thread-list")

    def create_source_thread(self, overrides=None):
        """
        Create a sample source cs_thread
        """
        thread = make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": str(self.course.id),
            "commentable_id": "test_topic",
            "user_id": str(self.user.id),
            "username": self.user.username,
            "created_at": "2015-04-28T00:00:00Z",
            "updated_at": "2015-04-28T11:11:11Z",
            "title": "Test Title",
            "body": "Test body",
            "votes": {"up_count": 4},
            "comments_count": 5,
            "unread_comments_count": 3,
        })

        thread.update(overrides or {})
        return thread

    def test_course_id_missing(self):
        response = self.client.get(self.url)
        self.assert_response_correct(
            response,
            400,
            {"field_errors": {"course_id": {"developer_message": "This field is required."}}}
        )

    def test_404(self):
        response = self.client.get(self.url, {"course_id": "non/existent/course"})
        self.assert_response_correct(
            response,
            404,
            {"developer_message": "Course not found."}
        )

    def test_basic(self):
        self.register_get_user_response(self.user, upvoted_ids=["test_thread"])
        source_threads = [
            self.create_source_thread({"user_id": str(self.author.id), "username": self.author.username})
        ]
        expected_threads = [self.expected_thread_data({
            "created_at": "2015-04-28T00:00:00Z",
            "updated_at": "2015-04-28T11:11:11Z",
            "vote_count": 4,
            "comment_count": 6,
            "can_delete": False,
            "unread_comment_count": 3,
            "voted": True,
            "author": self.author.username,
            "editable_fields": ["abuse_flagged", "copy_link", "following", "read", "voted"],
            "abuse_flagged_count": None,
        })]
        self.register_get_threads_response(source_threads, page=1, num_pages=2)
        response = self.client.get(self.url, {"course_id": str(self.course.id), "following": ""})
        expected_response = make_paginated_api_response(
            results=expected_threads,
            count=1,
            num_pages=2,
            next_link="http://testserver/api/discussion/v1/threads/?course_id=course-v1%3Ax%2By%2Bz&following=&page=2",
            previous_link=None
        )
        expected_response.update({"text_search_rewrite": None})
        self.assert_response_correct(
            response,
            200,
            expected_response
        )
        self.assert_last_query_params({
            "user_id": [str(self.user.id)],
            "course_id": [str(self.course.id)],
            "sort_key": ["activity"],
            "page": ["1"],
            "per_page": ["10"],
        })

    @ddt.data("unread", "unanswered", "unresponded")
    def test_view_query(self, query):
        threads = [make_minimal_cs_thread()]
        self.register_get_user_response(self.user)
        self.register_get_threads_response(threads, page=1, num_pages=1)
        self.client.get(
            self.url,
            {
                "course_id": str(self.course.id),
                "view": query,
            }
        )
        self.assert_last_query_params({
            "user_id": [str(self.user.id)],
            "course_id": [str(self.course.id)],
            "sort_key": ["activity"],
            "page": ["1"],
            "per_page": ["10"],
            query: ["true"],
        })

    def test_pagination(self):
        self.register_get_user_response(self.user)
        self.register_get_threads_response([], page=1, num_pages=1)
        response = self.client.get(
            self.url,
            {"course_id": str(self.course.id), "page": "18", "page_size": "4"}
        )
        self.assert_response_correct(
            response,
            404,
            {"developer_message": "Page not found (No results on this page)."}
        )
        self.assert_last_query_params({
            "user_id": [str(self.user.id)],
            "course_id": [str(self.course.id)],
            "sort_key": ["activity"],
            "page": ["18"],
            "per_page": ["4"],
        })

    def test_text_search(self):
        self.register_get_user_response(self.user)
        self.register_get_threads_search_response([], None, num_pages=0)
        response = self.client.get(
            self.url,
            {"course_id": str(self.course.id), "text_search": "test search string"}
        )

        expected_response = make_paginated_api_response(
            results=[], count=0, num_pages=0, next_link=None, previous_link=None
        )
        expected_response.update({"text_search_rewrite": None})
        self.assert_response_correct(
            response,
            200,
            expected_response
        )
        self.assert_last_query_params({
            "user_id": [str(self.user.id)],
            "course_id": [str(self.course.id)],
            "sort_key": ["activity"],
            "page": ["1"],
            "per_page": ["10"],
            "text": ["test search string"],
        })

    @ddt.data(True, "true", "1")
    def test_following_true(self, following):
        self.register_get_user_response(self.user)
        self.register_subscribed_threads_response(self.user, [], page=1, num_pages=0)
        response = self.client.get(
            self.url,
            {
                "course_id": str(self.course.id),
                "following": following,
            }
        )

        expected_response = make_paginated_api_response(
            results=[], count=0, num_pages=0, next_link=None, previous_link=None
        )
        expected_response.update({"text_search_rewrite": None})
        self.assert_response_correct(
            response,
            200,
            expected_response
        )
        assert urlparse(
            httpretty.last_request().path  # lint-amnesty, pylint: disable=no-member
        ).path == f"/api/v1/users/{self.user.id}/subscribed_threads"

    @ddt.data(False, "false", "0")
    def test_following_false(self, following):
        response = self.client.get(
            self.url,
            {
                "course_id": str(self.course.id),
                "following": following,
            }
        )
        self.assert_response_correct(
            response,
            400,
            {"field_errors": {
                "following": {"developer_message": "The value of the 'following' parameter must be true."}
            }}
        )

    def test_following_error(self):
        response = self.client.get(
            self.url,
            {
                "course_id": str(self.course.id),
                "following": "invalid-boolean",
            }
        )
        self.assert_response_correct(
            response,
            400,
            {"field_errors": {
                "following": {"developer_message": "Invalid Boolean Value."}
            }}
        )

    @ddt.data(
        ("last_activity_at", "activity"),
        ("comment_count", "comments"),
        ("vote_count", "votes")
    )
    @ddt.unpack
    def test_order_by(self, http_query, cc_query):
        """
        Tests the order_by parameter

        Arguments:
            http_query (str): Query string sent in the http request
            cc_query (str): Query string used for the comments client service
        """
        threads = [make_minimal_cs_thread()]
        self.register_get_user_response(self.user)
        self.register_get_threads_response(threads, page=1, num_pages=1)
        self.client.get(
            self.url,
            {
                "course_id": str(self.course.id),
                "order_by": http_query,
            }
        )
        self.assert_last_query_params({
            "user_id": [str(self.user.id)],
            "course_id": [str(self.course.id)],
            "page": ["1"],
            "per_page": ["10"],
            "sort_key": [cc_query],
        })

    def test_order_direction(self):
        """
        Test order direction, of which "desc" is the only valid option.  The
        option actually just gets swallowed, so it doesn't affect the params.
        """
        threads = [make_minimal_cs_thread()]
        self.register_get_user_response(self.user)
        self.register_get_threads_response(threads, page=1, num_pages=1)
        self.client.get(
            self.url,
            {
                "course_id": str(self.course.id),
                "order_direction": "desc",
            }
        )
        self.assert_last_query_params({
            "user_id": [str(self.user.id)],
            "course_id": [str(self.course.id)],
            "sort_key": ["activity"],
            "page": ["1"],
            "per_page": ["10"],
        })

    def test_mutually_exclusive(self):
        """
        Tests GET thread_list api does not allow filtering on mutually exclusive parameters
        """
        self.register_get_user_response(self.user)
        self.register_get_threads_search_response([], None, num_pages=0)
        response = self.client.get(self.url, {
            "course_id": str(self.course.id),
            "text_search": "test search string",
            "topic_id": "topic1, topic2",
        })
        self.assert_response_correct(
            response,
            400,
            {
                "developer_message": "The following query parameters are mutually exclusive: topic_id, "
                                     "text_search, following"
            }
        )

    def test_profile_image_requested_field(self):
        """
        Tests thread has user profile image details if called in requested_fields
        """
        user_2 = UserFactory.create(password=self.password)
        # Ensure that parental controls don't apply to this user
        user_2.profile.year_of_birth = 1970
        user_2.profile.save()
        source_threads = [
            self.create_source_thread(),
            self.create_source_thread({"user_id": str(user_2.id), "username": user_2.username}),
        ]

        self.register_get_user_response(self.user, upvoted_ids=["test_thread"])
        self.register_get_threads_response(source_threads, page=1, num_pages=1)
        self.create_profile_image(self.user, get_profile_image_storage())
        self.create_profile_image(user_2, get_profile_image_storage())

        response = self.client.get(
            self.url,
            {"course_id": str(self.course.id), "requested_fields": "profile_image"},
        )
        assert response.status_code == 200
        response_threads = json.loads(response.content.decode('utf-8'))['results']

        for response_thread in response_threads:
            expected_profile_data = self.get_expected_user_profile(response_thread['author'])
            response_users = response_thread['users']
            assert expected_profile_data == response_users[response_thread['author']]

    def test_profile_image_requested_field_anonymous_user(self):
        """
        Tests profile_image in requested_fields for thread created with anonymous user
        """
        source_threads = [
            self.create_source_thread(
                {"user_id": None, "username": None, "anonymous": True, "anonymous_to_peers": True}
            ),
        ]

        self.register_get_user_response(self.user, upvoted_ids=["test_thread"])
        self.register_get_threads_response(source_threads, page=1, num_pages=1)

        response = self.client.get(
            self.url,
            {"course_id": str(self.course.id), "requested_fields": "profile_image"},
        )
        assert response.status_code == 200
        response_thread = json.loads(response.content.decode('utf-8'))['results'][0]
        assert response_thread['author'] is None
        assert {} == response_thread['users']


@httpretty.activate
@disable_signal(api, 'thread_created')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class ThreadViewSetCreateTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for ThreadViewSet create"""
    def setUp(self):
        super().setUp()
        self.url = reverse("thread-list")

    def test_basic(self):
        self.register_get_user_response(self.user)
        cs_thread = make_minimal_cs_thread({
            "id": "test_thread",
            "username": self.user.username,
            "read": True,
        })
        self.register_post_thread_response(cs_thread)
        request_data = {
            "course_id": str(self.course.id),
            "topic_id": "test_topic",
            "type": "discussion",
            "title": "Test Title",
            "raw_body": "# Test \n This is a very long body that will be truncated for the preview.",
        }
        response = self.client.post(
            self.url,
            json.dumps(request_data),
            content_type="application/json"
        )
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data == self.expected_thread_data({
            "read": True,
            "raw_body": "# Test \n This is a very long body that will be truncated for the preview.",
            "preview_body": "Test This is a very long body that…",
            "rendered_body": "<h1>Test</h1>\n<p>This is a very long body that will be truncated for the preview.</p>",
        })
        assert parsed_body(httpretty.last_request()) == {
            'course_id': [str(self.course.id)],
            'commentable_id': ['test_topic'],
            'thread_type': ['discussion'],
            'title': ['Test Title'],
            'body': ['# Test \n This is a very long body that will be truncated for the preview.'],
            'user_id': [str(self.user.id)],
            'anonymous': ['False'],
            'anonymous_to_peers': ['False'],
        }

    def test_error(self):
        request_data = {
            "topic_id": "dummy",
            "type": "discussion",
            "title": "dummy",
            "raw_body": "dummy",
        }
        response = self.client.post(
            self.url,
            json.dumps(request_data),
            content_type="application/json"
        )
        expected_response_data = {
            "field_errors": {"course_id": {"developer_message": "This field is required."}}
        }
        assert response.status_code == 400
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data == expected_response_data


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
                'title', 'topic_id', 'type', 'voted'
            ],
            'created_at': 'Test Created Date',
            'updated_at': 'Test Updated Date',
            'comment_count': 1,
            'read': True,
            'response_count': 2,
        })
        assert parsed_body(httpretty.last_request()) == {
            'course_id': [str(self.course.id)],
            'commentable_id': ['test_topic'],
            'thread_type': ['discussion'],
            'title': ['Test Title'],
            'body': ['Edited body'],
            'user_id': [str(self.user.id)],
            'anonymous': ['False'],
            'anonymous_to_peers': ['False'],
            'closed': ['False'],
            'pinned': ['False'],
            'read': ['True'],
            'editing_user_id': [str(self.user.id)],
        }

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
                'title', 'topic_id', 'type', 'voted'
            ],
            'response_count': 2
        })

    def test_patch_read_non_owner_user(self):
        self.register_get_user_response(self.user)
        thread_owner_user = UserFactory.create(password=self.password)
        CourseEnrollmentFactory.create(user=thread_owner_user, course_id=self.course.id)
        self.register_get_user_response(thread_owner_user)
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
        assert response_data == self.expected_thread_data({
            'author': str(thread_owner_user.username),
            'comment_count': 1,
            'can_delete': False,
            'read': True,
            'editable_fields': ['abuse_flagged', 'copy_link', 'following', 'read', 'voted'],
            'response_count': 2
        })


@httpretty.activate
@disable_signal(api, 'thread_deleted')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class ThreadViewSetDeleteTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for ThreadViewSet delete"""
    def setUp(self):
        super().setUp()
        self.url = reverse("thread-detail", kwargs={"thread_id": "test_thread"})
        self.thread_id = "test_thread"

    def test_basic(self):
        self.register_get_user_response(self.user)
        cs_thread = make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": str(self.course.id),
            "username": self.user.username,
            "user_id": str(self.user.id),
        })
        self.register_get_thread_response(cs_thread)
        self.register_delete_thread_response(self.thread_id)
        response = self.client.delete(self.url)
        assert response.status_code == 204
        assert response.content == b''
        assert urlparse(httpretty.last_request().path).path == f"/api/v1/threads/{self.thread_id}"  # lint-amnesty, pylint: disable=no-member
        assert httpretty.last_request().method == 'DELETE'

    def test_delete_nonexistent_thread(self):
        self.register_get_thread_error_response(self.thread_id, 404)
        response = self.client.delete(self.url)
        assert response.status_code == 404


@ddt.ddt
@httpretty.activate
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class LearnerThreadViewAPITest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for LearnerThreadView list"""

    def setUp(self):
        """
        Sets up the test case
        """
        super().setUp()
        self.author = self.user
        self.remove_keys = [
            "abuse_flaggers",
            "body",
            "children",
            "commentable_id",
            "endorsed",
            "last_activity_at",
            "resp_total",
            "thread_type",
            "user_id",
            "username",
            "votes",
        ]
        self.replace_keys = [
            {"from": "unread_comments_count", "to": "unread_comment_count"},
            {"from": "comments_count", "to": "comment_count"},
        ]
        self.add_keys = [
            {"key": "author", "value": self.author.username},
            {"key": "abuse_flagged", "value": False},
            {"key": "author_label", "value": None},
            {"key": "can_delete", "value": True},
            {"key": "close_reason", "value": None},
            {
                "key": "comment_list_url",
                "value": "http://testserver/api/discussion/v1/comments/?thread_id=test_thread"
            },
            {
                "key": "editable_fields",
                "value": [
                    'abuse_flagged', 'anonymous', 'copy_link', 'following', 'raw_body',
                    'read', 'title', 'topic_id', 'type', 'voted'
                ]
            },
            {"key": "endorsed_comment_list_url", "value": None},
            {"key": "following", "value": False},
            {"key": "group_name", "value": None},
            {"key": "has_endorsed", "value": False},
            {"key": "last_edit", "value": None},
            {"key": "non_endorsed_comment_list_url", "value": None},
            {"key": "preview_body", "value": "Test body"},
            {"key": "raw_body", "value": "Test body"},

            {"key": "rendered_body", "value": "<p>Test body</p>"},
            {"key": "response_count", "value": 0},
            {"key": "topic_id", "value": "test_topic"},
            {"key": "type", "value": "discussion"},
            {"key": "users", "value": {
                self.user.username: {
                    "profile": {
                        "image": {
                            "has_image": False,
                            "image_url_full": "http://testserver/static/default_500.png",
                            "image_url_large": "http://testserver/static/default_120.png",
                            "image_url_medium": "http://testserver/static/default_50.png",
                            "image_url_small": "http://testserver/static/default_30.png",
                        }
                    }
                }
            }},
            {"key": "vote_count", "value": 4},
            {"key": "voted", "value": False},

        ]
        self.url = reverse("discussion_learner_threads", kwargs={'course_id': str(self.course.id)})

    def update_thread(self, thread):
        """
        This function updates the thread by adding and remove some keys.
        Value of these keys has been defined in setUp function
        """
        for element in self.add_keys:
            thread[element['key']] = element['value']
        for pair in self.replace_keys:
            thread[pair['to']] = thread.pop(pair['from'])
        for key in self.remove_keys:
            thread.pop(key)
        thread['comment_count'] += 1
        return thread

    def test_basic(self):
        """
        Tests the data is fetched correctly

        Note: test_basic is required as the name because DiscussionAPIViewTestMixin
              calls this test case automatically
        """
        self.register_get_user_response(self.user)
        expected_cs_comments_response = {
            "collection": [make_minimal_cs_thread({
                "id": "test_thread",
                "course_id": str(self.course.id),
                "commentable_id": "test_topic",
                "user_id": str(self.user.id),
                "username": self.user.username,
                "created_at": "2015-04-28T00:00:00Z",
                "updated_at": "2015-04-28T11:11:11Z",
                "title": "Test Title",
                "body": "Test body",
                "votes": {"up_count": 4},
                "comments_count": 5,
                "unread_comments_count": 3,
            })],
            "page": 1,
            "num_pages": 1,
        }
        self.register_user_active_threads(self.user.id, expected_cs_comments_response)
        self.url += f"?username={self.user.username}"
        response = self.client.get(self.url)
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        expected_api_response = expected_cs_comments_response['collection']

        for thread in expected_api_response:
            self.update_thread(thread)

        assert response_data['results'] == expected_api_response
        assert response_data['pagination'] == {
            "next": None,
            "previous": None,
            "count": 1,
            "num_pages": 1,
        }

    def test_no_username_given(self):
        """
        Tests that 404 response is returned when no username is passed
        """
        response = self.client.get(self.url)
        assert response.status_code == 404

    def test_not_authenticated(self):
        """
        This test is called by DiscussionAPIViewTestMixin and is not required in
        our case
        """
        assert True

    @ddt.data("None", "discussion", "question")
    def test_thread_type_by(self, thread_type):
        """
        Tests the thread_type parameter

        Arguments:
            thread_type (str): Value of thread_type can be 'None',
                          'discussion' and 'question'
        """
        threads = [make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": str(self.course.id),
            "commentable_id": "test_topic",
            "user_id": str(self.user.id),
            "username": self.user.username,
            "created_at": "2015-04-28T00:00:00Z",
            "updated_at": "2015-04-28T11:11:11Z",
            "title": "Test Title",
            "body": "Test body",
            "votes": {"up_count": 4},
            "comments_count": 5,
            "unread_comments_count": 3,
        })]
        expected_cs_comments_response = {
            "collection": threads,
            "page": 1,
            "num_pages": 1,
        }
        self.register_get_user_response(self.user)
        self.register_user_active_threads(self.user.id, expected_cs_comments_response)
        response = self.client.get(
            self.url,
            {
                "course_id": str(self.course.id),
                "username": self.user.username,
                "thread_type": thread_type,
            }
        )
        assert response.status_code == 200
        self.assert_last_query_params({
            "user_id": [str(self.user.id)],
            "course_id": [str(self.course.id)],
            "page": ["1"],
            "per_page": ["10"],
            "thread_type": [thread_type],
            "sort_key": ['activity'],
            "count_flagged": ["False"]
        })

    @ddt.data(
        ("last_activity_at", "activity"),
        ("comment_count", "comments"),
        ("vote_count", "votes")
    )
    @ddt.unpack
    def test_order_by(self, http_query, cc_query):
        """
        Tests the order_by parameter for active threads

        Arguments:
            http_query (str): Query string sent in the http request
            cc_query (str): Query string used for the comments client service
        """
        threads = [make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": str(self.course.id),
            "commentable_id": "test_topic",
            "user_id": str(self.user.id),
            "username": self.user.username,
            "created_at": "2015-04-28T00:00:00Z",
            "updated_at": "2015-04-28T11:11:11Z",
            "title": "Test Title",
            "body": "Test body",
            "votes": {"up_count": 4},
            "comments_count": 5,
            "unread_comments_count": 3,
        })]
        expected_cs_comments_response = {
            "collection": threads,
            "page": 1,
            "num_pages": 1,
        }
        self.register_get_user_response(self.user)
        self.register_user_active_threads(self.user.id, expected_cs_comments_response)
        response = self.client.get(
            self.url,
            {
                "course_id": str(self.course.id),
                "username": self.user.username,
                "order_by": http_query,
            }
        )
        assert response.status_code == 200
        self.assert_last_query_params({
            "user_id": [str(self.user.id)],
            "course_id": [str(self.course.id)],
            "page": ["1"],
            "per_page": ["10"],
            "sort_key": [cc_query],
            "count_flagged": ["False"]
        })

    @ddt.data("flagged", "unanswered", "unread", "unresponded")
    def test_status_by(self, post_status):
        """
        Tests the post_status parameter

        Arguments:
            post_status (str): Value of post_status can be 'flagged',
                          'unanswered' and 'unread'
        """
        threads = [make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": str(self.course.id),
            "commentable_id": "test_topic",
            "user_id": str(self.user.id),
            "username": self.user.username,
            "created_at": "2015-04-28T00:00:00Z",
            "updated_at": "2015-04-28T11:11:11Z",
            "title": "Test Title",
            "body": "Test body",
            "votes": {"up_count": 4},
            "comments_count": 5,
            "unread_comments_count": 3,
        })]
        expected_cs_comments_response = {
            "collection": threads,
            "page": 1,
            "num_pages": 1,
        }
        self.register_get_user_response(self.user)
        self.register_user_active_threads(self.user.id, expected_cs_comments_response)
        response = self.client.get(
            self.url,
            {
                "course_id": str(self.course.id),
                "username": self.user.username,
                "status": post_status,
            }
        )
        if post_status == "flagged":
            assert response.status_code == 403
        else:
            assert response.status_code == 200
            self.assert_last_query_params({
                "user_id": [str(self.user.id)],
                "course_id": [str(self.course.id)],
                "page": ["1"],
                "per_page": ["10"],
                post_status: ['True'],
                "sort_key": ['activity'],
                "count_flagged": ["False"]
            })


@ddt.ddt
@httpretty.activate
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CommentViewSetListTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase, ProfileImageTestMixin):
    """Tests for CommentViewSet list"""
    def setUp(self):
        super().setUp()
        self.author = UserFactory.create()
        self.url = reverse("comment-list")
        self.thread_id = "test_thread"
        self.storage = get_profile_image_storage()

    def create_source_comment(self, overrides=None):
        """
        Create a sample source cs_comment
        """
        comment = make_minimal_cs_comment({
            "id": "test_comment",
            "thread_id": self.thread_id,
            "user_id": str(self.user.id),
            "username": self.user.username,
            "created_at": "2015-05-11T00:00:00Z",
            "updated_at": "2015-05-11T11:11:11Z",
            "body": "Test body",
            "votes": {"up_count": 4},
        })

        comment.update(overrides or {})
        return comment

    def make_minimal_cs_thread(self, overrides=None):
        """
        Create a thread with the given overrides, plus the course_id if not
        already in overrides.
        """
        overrides = overrides.copy() if overrides else {}
        overrides.setdefault("course_id", str(self.course.id))
        return make_minimal_cs_thread(overrides)

    def expected_response_comment(self, overrides=None):
        """
        create expected response data
        """
        response_data = {
            "id": "test_comment",
            "thread_id": self.thread_id,
            "parent_id": None,
            "author": self.author.username,
            "author_label": None,
            "created_at": "1970-01-01T00:00:00Z",
            "updated_at": "1970-01-01T00:00:00Z",
            "raw_body": "dummy",
            "rendered_body": "<p>dummy</p>",
            "endorsed": False,
            "endorsed_by": None,
            "endorsed_by_label": None,
            "endorsed_at": None,
            "abuse_flagged": False,
            "abuse_flagged_any_user": None,
            "voted": False,
            "vote_count": 0,
            "children": [],
            "editable_fields": ["abuse_flagged", "voted"],
            "child_count": 0,
            "can_delete": True,
            "anonymous": False,
            "anonymous_to_peers": False,
            "last_edit": None,
        }
        response_data.update(overrides or {})
        return response_data

    def test_thread_id_missing(self):
        response = self.client.get(self.url)
        self.assert_response_correct(
            response,
            400,
            {"field_errors": {"thread_id": {"developer_message": "This field is required."}}}
        )

    def test_404(self):
        self.register_get_thread_error_response(self.thread_id, 404)
        response = self.client.get(self.url, {"thread_id": self.thread_id})
        self.assert_response_correct(
            response,
            404,
            {"developer_message": "Thread not found."}
        )

    def test_basic(self):
        self.register_get_user_response(self.user, upvoted_ids=["test_comment"])
        source_comments = [
            self.create_source_comment({"user_id": str(self.author.id), "username": self.author.username})
        ]
        expected_comments = [self.expected_response_comment(overrides={
            "voted": True,
            "vote_count": 4,
            "raw_body": "Test body",
            "can_delete": False,
            "rendered_body": "<p>Test body</p>",
            "created_at": "2015-05-11T00:00:00Z",
            "updated_at": "2015-05-11T11:11:11Z",
        })]
        self.register_get_thread_response({
            "id": self.thread_id,
            "course_id": str(self.course.id),
            "thread_type": "discussion",
            "children": source_comments,
            "resp_total": 100,
        })
        response = self.client.get(self.url, {"thread_id": self.thread_id})
        next_link = "http://testserver/api/discussion/v1/comments/?page=2&thread_id={}".format(
            self.thread_id
        )
        self.assert_response_correct(
            response,
            200,
            make_paginated_api_response(
                results=expected_comments, count=100, num_pages=10, next_link=next_link, previous_link=None
            )
        )
        self.assert_query_params_equal(
            httpretty.httpretty.latest_requests[-2],
            {
                "resp_skip": ["0"],
                "resp_limit": ["10"],
                "user_id": [str(self.user.id)],
                "mark_as_read": ["False"],
                "recursive": ["False"],
                "with_responses": ["True"],
            }
        )

    def test_pagination(self):
        """
        Test that pagination parameters are correctly plumbed through to the
        comments service and that a 404 is correctly returned if a page past the
        end is requested
        """
        self.register_get_user_response(self.user)
        self.register_get_thread_response(make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": str(self.course.id),
            "thread_type": "discussion",
            "resp_total": 10,
        }))
        response = self.client.get(
            self.url,
            {"thread_id": self.thread_id, "page": "18", "page_size": "4"}
        )
        self.assert_response_correct(
            response,
            404,
            {"developer_message": "Page not found (No results on this page)."}
        )
        self.assert_query_params_equal(
            httpretty.httpretty.latest_requests[-2],
            {
                "resp_skip": ["68"],
                "resp_limit": ["4"],
                "user_id": [str(self.user.id)],
                "mark_as_read": ["False"],
                "recursive": ["False"],
                "with_responses": ["True"],
            }
        )

    @ddt.data(
        (True, "endorsed_comment"),
        ("true", "endorsed_comment"),
        ("1", "endorsed_comment"),
        (False, "non_endorsed_comment"),
        ("false", "non_endorsed_comment"),
        ("0", "non_endorsed_comment"),
    )
    @ddt.unpack
    def test_question_content(self, endorsed, comment_id):
        self.register_get_user_response(self.user)
        thread = self.make_minimal_cs_thread({
            "thread_type": "question",
            "endorsed_responses": [make_minimal_cs_comment({
                "id": "endorsed_comment",
                "user_id": self.user.id,
                "username": self.user.username,
            })],
            "non_endorsed_responses": [make_minimal_cs_comment({
                "id": "non_endorsed_comment",
                "user_id": self.user.id,
                "username": self.user.username,
            })],
            "non_endorsed_resp_total": 1,
        })
        self.register_get_thread_response(thread)
        response = self.client.get(self.url, {
            "thread_id": thread["id"],
            "endorsed": endorsed,
        })
        parsed_content = json.loads(response.content.decode('utf-8'))
        assert parsed_content['results'][0]['id'] == comment_id

    def test_question_invalid_endorsed(self):
        response = self.client.get(self.url, {
            "thread_id": self.thread_id,
            "endorsed": "invalid-boolean"
        })
        self.assert_response_correct(
            response,
            400,
            {"field_errors": {
                "endorsed": {"developer_message": "Invalid Boolean Value."}
            }}
        )

    def test_question_missing_endorsed(self):
        self.register_get_user_response(self.user)
        thread = self.make_minimal_cs_thread({
            "thread_type": "question",
            "endorsed_responses": [make_minimal_cs_comment({"id": "endorsed_comment"})],
            "non_endorsed_responses": [make_minimal_cs_comment({"id": "non_endorsed_comment"})],
            "non_endorsed_resp_total": 1,
        })
        self.register_get_thread_response(thread)
        response = self.client.get(self.url, {
            "thread_id": thread["id"]
        })
        self.assert_response_correct(
            response,
            400,
            {"field_errors": {
                "endorsed": {"developer_message": "This field is required for question threads."}
            }}
        )

    def test_child_comments_count(self):
        self.register_get_user_response(self.user)
        response_1 = make_minimal_cs_comment({
            "id": "test_response_1",
            "thread_id": self.thread_id,
            "user_id": str(self.author.id),
            "username": self.author.username,
            "child_count": 2,
        })
        response_2 = make_minimal_cs_comment({
            "id": "test_response_2",
            "thread_id": self.thread_id,
            "user_id": str(self.author.id),
            "username": self.author.username,
            "child_count": 3,
        })
        thread = self.make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": str(self.course.id),
            "thread_type": "discussion",
            "children": [response_1, response_2],
            "resp_total": 2,
            "comments_count": 8,
            "unread_comments_count": 0,

        })
        self.register_get_thread_response(thread)
        response = self.client.get(self.url, {"thread_id": self.thread_id})
        expected_comments = [
            self.expected_response_comment(overrides={"id": "test_response_1", "child_count": 2, "can_delete": False}),
            self.expected_response_comment(overrides={"id": "test_response_2", "child_count": 3, "can_delete": False}),
        ]
        self.assert_response_correct(
            response,
            200,
            {
                "results": expected_comments,
                "pagination": {
                    "count": 2,
                    "next": None,
                    "num_pages": 1,
                    "previous": None,
                }
            }
        )

    def test_profile_image_requested_field(self):
        """
        Tests all comments retrieved have user profile image details if called in requested_fields
        """
        source_comments = [self.create_source_comment()]
        self.register_get_thread_response({
            "id": self.thread_id,
            "course_id": str(self.course.id),
            "thread_type": "discussion",
            "children": source_comments,
            "resp_total": 100,
        })
        self.register_get_user_response(self.user, upvoted_ids=["test_comment"])
        self.create_profile_image(self.user, get_profile_image_storage())

        response = self.client.get(self.url, {"thread_id": self.thread_id, "requested_fields": "profile_image"})
        assert response.status_code == 200
        response_comments = json.loads(response.content.decode('utf-8'))['results']
        for response_comment in response_comments:
            expected_profile_data = self.get_expected_user_profile(response_comment['author'])
            response_users = response_comment['users']
            assert expected_profile_data == response_users[response_comment['author']]

    def test_profile_image_requested_field_endorsed_comments(self):
        """
        Tests all comments have user profile image details for both author and endorser
        if called in requested_fields for endorsed threads
        """
        endorser_user = UserFactory.create(password=self.password)
        # Ensure that parental controls don't apply to this user
        endorser_user.profile.year_of_birth = 1970
        endorser_user.profile.save()

        self.register_get_user_response(self.user)
        thread = self.make_minimal_cs_thread({
            "thread_type": "question",
            "endorsed_responses": [make_minimal_cs_comment({
                "id": "endorsed_comment",
                "user_id": self.user.id,
                "username": self.user.username,
                "endorsed": True,
                "endorsement": {"user_id": endorser_user.id, "time": "2016-05-10T08:51:28Z"},
            })],
            "non_endorsed_responses": [make_minimal_cs_comment({
                "id": "non_endorsed_comment",
                "user_id": self.user.id,
                "username": self.user.username,
            })],
            "non_endorsed_resp_total": 1,
        })
        self.register_get_thread_response(thread)
        self.create_profile_image(self.user, get_profile_image_storage())
        self.create_profile_image(endorser_user, get_profile_image_storage())

        response = self.client.get(self.url, {
            "thread_id": thread["id"],
            "endorsed": True,
            "requested_fields": "profile_image",
        })
        assert response.status_code == 200
        response_comments = json.loads(response.content.decode('utf-8'))['results']
        for response_comment in response_comments:
            expected_author_profile_data = self.get_expected_user_profile(response_comment['author'])
            expected_endorser_profile_data = self.get_expected_user_profile(response_comment['endorsed_by'])
            response_users = response_comment['users']
            assert expected_author_profile_data == response_users[response_comment['author']]
            assert expected_endorser_profile_data == response_users[response_comment['endorsed_by']]

    def test_profile_image_request_for_null_endorsed_by(self):
        """
        Tests if 'endorsed' is True but 'endorsed_by' is null, the api does not crash.
        This is the case for some old/stale data in prod/stage environments.
        """
        self.register_get_user_response(self.user)
        thread = self.make_minimal_cs_thread({
            "thread_type": "question",
            "endorsed_responses": [make_minimal_cs_comment({
                "id": "endorsed_comment",
                "user_id": self.user.id,
                "username": self.user.username,
                "endorsed": True,
            })],
            "non_endorsed_resp_total": 0,
        })
        self.register_get_thread_response(thread)
        self.create_profile_image(self.user, get_profile_image_storage())

        response = self.client.get(self.url, {
            "thread_id": thread["id"],
            "endorsed": True,
            "requested_fields": "profile_image",
        })
        assert response.status_code == 200
        response_comments = json.loads(response.content.decode('utf-8'))['results']
        for response_comment in response_comments:
            expected_author_profile_data = self.get_expected_user_profile(response_comment['author'])
            response_users = response_comment['users']
            assert expected_author_profile_data == response_users[response_comment['author']]
            assert response_comment['endorsed_by'] not in response_users


@httpretty.activate
@disable_signal(api, 'comment_deleted')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CommentViewSetDeleteTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for ThreadViewSet delete"""

    def setUp(self):
        super().setUp()
        self.url = reverse("comment-detail", kwargs={"comment_id": "test_comment"})
        self.comment_id = "test_comment"

    def test_basic(self):
        self.register_get_user_response(self.user)
        cs_thread = make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": str(self.course.id),
        })
        self.register_get_thread_response(cs_thread)
        cs_comment = make_minimal_cs_comment({
            "id": self.comment_id,
            "course_id": cs_thread["course_id"],
            "thread_id": cs_thread["id"],
            "username": self.user.username,
            "user_id": str(self.user.id),
        })
        self.register_get_comment_response(cs_comment)
        self.register_delete_comment_response(self.comment_id)
        response = self.client.delete(self.url)
        assert response.status_code == 204
        assert response.content == b''
        assert urlparse(httpretty.last_request().path).path == f"/api/v1/comments/{self.comment_id}"  # lint-amnesty, pylint: disable=no-member
        assert httpretty.last_request().method == 'DELETE'

    def test_delete_nonexistent_comment(self):
        self.register_get_comment_error_response(self.comment_id, 404)
        response = self.client.delete(self.url)
        assert response.status_code == 404


@httpretty.activate
@disable_signal(api, 'comment_created')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CommentViewSetCreateTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for CommentViewSet create"""
    def setUp(self):
        super().setUp()
        self.url = reverse("comment-list")

    def test_basic(self):
        self.register_get_user_response(self.user)
        self.register_thread()
        self.register_comment()
        request_data = {
            "thread_id": "test_thread",
            "raw_body": "Test body",
        }
        expected_response_data = {
            "id": "test_comment",
            "thread_id": "test_thread",
            "parent_id": None,
            "author": self.user.username,
            "author_label": None,
            "created_at": "1970-01-01T00:00:00Z",
            "updated_at": "1970-01-01T00:00:00Z",
            "raw_body": "Test body",
            "rendered_body": "<p>Test body</p>",
            "endorsed": False,
            "endorsed_by": None,
            "endorsed_by_label": None,
            "endorsed_at": None,
            "abuse_flagged": False,
            "abuse_flagged_any_user": None,
            "voted": False,
            "vote_count": 0,
            "children": [],
            "editable_fields": ["abuse_flagged", "anonymous", "raw_body", "voted"],
            "child_count": 0,
            "can_delete": True,
            "anonymous": False,
            "anonymous_to_peers": False,
            "last_edit": None,
        }
        response = self.client.post(
            self.url,
            json.dumps(request_data),
            content_type="application/json"
        )
        assert response.status_code == 200
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data == expected_response_data
        assert urlparse(httpretty.last_request().path).path == '/api/v1/threads/test_thread/comments'  # lint-amnesty, pylint: disable=no-member
        assert parsed_body(httpretty.last_request()) == {
            'course_id': [str(self.course.id)],
            'body': ['Test body'],
            'user_id': [str(self.user.id)],
            'anonymous': ['False'],
            'anonymous_to_peers': ['False'],
        }

    def test_error(self):
        response = self.client.post(
            self.url,
            json.dumps({}),
            content_type="application/json"
        )
        expected_response_data = {
            "field_errors": {"thread_id": {"developer_message": "This field is required."}}
        }
        assert response.status_code == 400
        response_data = json.loads(response.content.decode('utf-8'))
        assert response_data == expected_response_data

    def test_closed_thread(self):
        self.register_get_user_response(self.user)
        self.register_thread({"closed": True})
        self.register_comment()
        request_data = {
            "thread_id": "test_thread",
            "raw_body": "Test body"
        }
        response = self.client.post(
            self.url,
            json.dumps(request_data),
            content_type="application/json"
        )
        assert response.status_code == 403


@ddt.ddt
@disable_signal(api, 'comment_edited')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CommentViewSetPartialUpdateTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase, PatchMediaTypeMixin):
    """Tests for CommentViewSet partial_update"""
    def setUp(self):
        self.unsupported_media_type = JSONParser.media_type
        super().setUp()
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.reset)
        self.addCleanup(httpretty.disable)
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
            'editable_fields': ['abuse_flagged', 'anonymous', 'raw_body', 'voted'],
            'created_at': 'Test Created Date',
            'updated_at': 'Test Updated Date'
        })
        assert parsed_body(httpretty.last_request()) == {
            'body': ['Edited body'],
            'course_id': [str(self.course.id)],
            'user_id': [str(self.user.id)],
            'anonymous': ['False'],
            'anonymous_to_peers': ['False'],
            'endorsed': ['False'],
            'editing_user_id': [str(self.user.id)],
        }

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


@httpretty.activate
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class ThreadViewSetRetrieveTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase, ProfileImageTestMixin):
    """Tests for ThreadViewSet Retrieve"""
    def setUp(self):
        super().setUp()
        self.url = reverse("thread-detail", kwargs={"thread_id": "test_thread"})
        self.thread_id = "test_thread"

    def test_basic(self):
        self.register_get_user_response(self.user)
        cs_thread = make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": str(self.course.id),
            "commentable_id": "test_topic",
            "username": self.user.username,
            "user_id": str(self.user.id),
            "title": "Test Title",
            "body": "Test body",
        })
        self.register_get_thread_response(cs_thread)
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert json.loads(response.content.decode('utf-8')) == self.expected_thread_data({'unread_comment_count': 1})
        assert httpretty.last_request().method == 'GET'

    def test_retrieve_nonexistent_thread(self):
        self.register_get_thread_error_response(self.thread_id, 404)
        response = self.client.get(self.url)
        assert response.status_code == 404

    def test_profile_image_requested_field(self):
        """
        Tests thread has user profile image details if called in requested_fields
        """
        self.register_get_user_response(self.user)
        cs_thread = make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": str(self.course.id),
            "username": self.user.username,
            "user_id": str(self.user.id),
        })
        self.register_get_thread_response(cs_thread)
        self.create_profile_image(self.user, get_profile_image_storage())
        response = self.client.get(self.url, {"requested_fields": "profile_image"})
        assert response.status_code == 200
        expected_profile_data = self.get_expected_user_profile(self.user.username)
        response_users = json.loads(response.content.decode('utf-8'))['users']
        assert expected_profile_data == response_users[self.user.username]


@httpretty.activate
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CommentViewSetRetrieveTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase, ProfileImageTestMixin):
    """Tests for CommentViewSet Retrieve"""
    def setUp(self):
        super().setUp()
        self.url = reverse("comment-detail", kwargs={"comment_id": "test_comment"})
        self.thread_id = "test_thread"
        self.comment_id = "test_comment"

    def make_comment_data(self, comment_id, parent_id=None, children=[]):  # pylint: disable=W0102
        """
        Returns comment dict object as returned by comments service
        """
        return make_minimal_cs_comment({
            "id": comment_id,
            "parent_id": parent_id,
            "course_id": str(self.course.id),
            "thread_id": self.thread_id,
            "thread_type": "discussion",
            "username": self.user.username,
            "user_id": str(self.user.id),
            "created_at": "2015-06-03T00:00:00Z",
            "updated_at": "2015-06-03T00:00:00Z",
            "body": "Original body",
            "children": children,
        })

    def test_basic(self):
        self.register_get_user_response(self.user)
        cs_comment_child = self.make_comment_data("test_child_comment", self.comment_id, children=[])
        cs_comment = self.make_comment_data(self.comment_id, None, [cs_comment_child])
        cs_thread = make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": str(self.course.id),
            "children": [cs_comment],
        })
        self.register_get_thread_response(cs_thread)
        self.register_get_comment_response(cs_comment)

        expected_response_data = {
            "id": "test_child_comment",
            "parent_id": self.comment_id,
            "thread_id": self.thread_id,
            "author": self.user.username,
            "author_label": None,
            "raw_body": "Original body",
            "rendered_body": "<p>Original body</p>",
            "created_at": "2015-06-03T00:00:00Z",
            "updated_at": "2015-06-03T00:00:00Z",
            "children": [],
            "endorsed_at": None,
            "endorsed": False,
            "endorsed_by": None,
            "endorsed_by_label": None,
            "voted": False,
            "vote_count": 0,
            "abuse_flagged": False,
            "abuse_flagged_any_user": None,
            "editable_fields": ["abuse_flagged", "anonymous", "raw_body", "voted"],
            "child_count": 0,
            "can_delete": True,
            "anonymous": False,
            "anonymous_to_peers": False,
            "last_edit": None,
        }

        response = self.client.get(self.url)
        assert response.status_code == 200
        assert json.loads(response.content.decode('utf-8'))['results'][0] == expected_response_data

    def test_retrieve_nonexistent_comment(self):
        self.register_get_comment_error_response(self.comment_id, 404)
        response = self.client.get(self.url)
        assert response.status_code == 404

    def test_pagination(self):
        """
        Test that pagination parameters are correctly plumbed through to the
        comments service and that a 404 is correctly returned if a page past the
        end is requested
        """
        self.register_get_user_response(self.user)
        cs_comment_child = self.make_comment_data("test_child_comment", self.comment_id, children=[])
        cs_comment = self.make_comment_data(self.comment_id, None, [cs_comment_child])
        cs_thread = make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": str(self.course.id),
            "children": [cs_comment],
        })
        self.register_get_thread_response(cs_thread)
        self.register_get_comment_response(cs_comment)
        response = self.client.get(
            self.url,
            {"comment_id": self.comment_id, "page": "18", "page_size": "4"}
        )
        self.assert_response_correct(
            response,
            404,
            {"developer_message": "Page not found (No results on this page)."}
        )

    def test_profile_image_requested_field(self):
        """
        Tests all comments retrieved have user profile image details if called in requested_fields
        """
        self.register_get_user_response(self.user)
        cs_comment_child = self.make_comment_data('test_child_comment', self.comment_id, children=[])
        cs_comment = self.make_comment_data(self.comment_id, None, [cs_comment_child])
        cs_thread = make_minimal_cs_thread({
            'id': self.thread_id,
            'course_id': str(self.course.id),
            'children': [cs_comment],
        })
        self.register_get_thread_response(cs_thread)
        self.register_get_comment_response(cs_comment)
        self.create_profile_image(self.user, get_profile_image_storage())

        response = self.client.get(self.url, {'requested_fields': 'profile_image'})
        assert response.status_code == 200
        response_comments = json.loads(response.content.decode('utf-8'))['results']

        for response_comment in response_comments:
            expected_profile_data = self.get_expected_user_profile(response_comment['author'])
            response_users = response_comment['users']
            assert expected_profile_data == response_users[response_comment['author']]


@ddt.ddt
class CourseDiscussionSettingsAPIViewTest(APITestCase, UrlResetMixin, ModuleStoreTestCase):
    """
    Test the course discussion settings handler API endpoint.
    """
    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(
            org="x",
            course="y",
            run="z",
            start=datetime.now(UTC),
            discussion_topics={"Test Topic": {"id": "test_topic"}}
        )
        self.path = reverse('discussion_course_settings', kwargs={'course_id': str(self.course.id)})
        self.password = 'edx'
        self.user = UserFactory(username='staff', password=self.password, is_staff=True)

    def _get_oauth_headers(self, user):
        """Return the OAuth headers for testing OAuth authentication"""
        access_token = AccessTokenFactory.create(user=user, application=ApplicationFactory()).token
        headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + access_token
        }
        return headers

    def _login_as_staff(self):
        """Log the client in as the staff."""
        self.client.login(username=self.user.username, password=self.password)

    def _login_as_discussion_staff(self):
        user = UserFactory(username='abc', password='abc')
        role = Role.objects.create(name='Administrator', course_id=self.course.id)
        role.users.set([user])
        self.client.login(username=user.username, password='abc')

    def _create_divided_discussions(self):
        """Create some divided discussions for testing."""
        divided_inline_discussions = ['Topic A', ]
        divided_course_wide_discussions = ['Topic B', ]
        divided_discussions = divided_inline_discussions + divided_course_wide_discussions

        ItemFactory.create(
            parent=self.course,
            category='discussion',
            discussion_id=topic_name_to_id(self.course, 'Topic A'),
            discussion_category='Chapter',
            discussion_target='Discussion',
            start=datetime.now()
        )
        discussion_topics = {
            "Topic B": {"id": "Topic B"},
        }
        config_course_cohorts(self.course, is_cohorted=True)
        config_course_discussions(
            self.course,
            discussion_topics=discussion_topics,
            divided_discussions=divided_discussions
        )
        return divided_inline_discussions, divided_course_wide_discussions

    def _get_expected_response(self):
        """Return the default expected response before any changes to the discussion settings."""
        return {
            'always_divide_inline_discussions': False,
            'divided_inline_discussions': [],
            'divided_course_wide_discussions': [],
            'id': 1,
            'division_scheme': 'cohort',
            'available_division_schemes': ['cohort'],
            'reported_content_email_notifications': False,
            'reported_content_email_notifications_flag': False,
        }

    def patch_request(self, data, headers=None):
        headers = headers if headers else {}
        return self.client.patch(self.path, json.dumps(data), content_type='application/merge-patch+json', **headers)

    def _assert_current_settings(self, expected_response):
        """Validate the current discussion settings against the expected response."""
        response = self.client.get(self.path)
        assert response.status_code == 200
        content = json.loads(response.content.decode('utf-8'))
        assert content == expected_response

    def _assert_patched_settings(self, data, expected_response):
        """Validate the patched settings against the expected response."""
        response = self.patch_request(data)
        assert response.status_code == 204
        self._assert_current_settings(expected_response)

    @ddt.data('get', 'patch')
    def test_authentication_required(self, method):
        """Test and verify that authentication is required for this endpoint."""
        self.client.logout()
        response = getattr(self.client, method)(self.path)
        assert response.status_code == 401

    @ddt.data(
        {'is_staff': False, 'get_status': 403, 'put_status': 403},
        {'is_staff': True, 'get_status': 200, 'put_status': 204},
    )
    @ddt.unpack
    def test_oauth(self, is_staff, get_status, put_status):
        """Test that OAuth authentication works for this endpoint."""
        user = UserFactory(is_staff=is_staff)
        headers = self._get_oauth_headers(user)
        self.client.logout()

        response = self.client.get(self.path, **headers)
        assert response.status_code == get_status

        response = self.patch_request(
            {'always_divide_inline_discussions': True}, headers
        )
        assert response.status_code == put_status

    def test_non_existent_course_id(self):
        """Test the response when this endpoint is passed a non-existent course id."""
        self._login_as_staff()
        response = self.client.get(
            reverse('discussion_course_settings', kwargs={
                'course_id': 'course-v1:a+b+c'
            })
        )
        assert response.status_code == 404

    def test_patch_request_by_discussion_staff(self):
        """Test the response when patch request is sent by a user with discussions staff role."""
        self._login_as_discussion_staff()
        response = self.patch_request(
            {'always_divide_inline_discussions': True}
        )
        assert response.status_code == 403

    def test_get_request_by_discussion_staff(self):
        """Test the response when get request is sent by a user with discussions staff role."""
        self._login_as_discussion_staff()
        divided_inline_discussions, divided_course_wide_discussions = self._create_divided_discussions()
        response = self.client.get(self.path)
        assert response.status_code == 200
        expected_response = self._get_expected_response()
        expected_response['divided_course_wide_discussions'] = [
            topic_name_to_id(self.course, name) for name in divided_course_wide_discussions
        ]
        expected_response['divided_inline_discussions'] = [
            topic_name_to_id(self.course, name) for name in divided_inline_discussions
        ]
        content = json.loads(response.content.decode('utf-8'))
        assert content == expected_response

    def test_get_request_by_non_staff_user(self):
        """Test the response when get request is sent by a regular user with no staff role."""
        user = UserFactory(username='abc', password='abc')
        self.client.login(username=user.username, password='abc')
        response = self.client.get(self.path)
        assert response.status_code == 403

    def test_patch_request_by_non_staff_user(self):
        """Test the response when patch request is sent by a regular user with no staff role."""
        user = UserFactory(username='abc', password='abc')
        self.client.login(username=user.username, password='abc')
        response = self.patch_request(
            {'always_divide_inline_discussions': True}
        )
        assert response.status_code == 403

    def test_get_settings(self):
        """Test the current discussion settings against the expected response."""
        divided_inline_discussions, divided_course_wide_discussions = self._create_divided_discussions()
        self._login_as_staff()
        response = self.client.get(self.path)
        assert response.status_code == 200
        expected_response = self._get_expected_response()
        expected_response['divided_course_wide_discussions'] = [
            topic_name_to_id(self.course, name) for name in divided_course_wide_discussions
        ]
        expected_response['divided_inline_discussions'] = [
            topic_name_to_id(self.course, name) for name in divided_inline_discussions
        ]
        content = json.loads(response.content.decode('utf-8'))
        assert content == expected_response

    def test_available_schemes(self):
        """Test the available division schemes against the expected response."""
        config_course_cohorts(self.course, is_cohorted=False)
        self._login_as_staff()
        expected_response = self._get_expected_response()
        expected_response['available_division_schemes'] = []
        self._assert_current_settings(expected_response)

        CourseModeFactory.create(course_id=self.course.id, mode_slug=CourseMode.AUDIT)
        CourseModeFactory.create(course_id=self.course.id, mode_slug=CourseMode.VERIFIED)

        expected_response['available_division_schemes'] = [CourseDiscussionSettings.ENROLLMENT_TRACK]
        self._assert_current_settings(expected_response)

        config_course_cohorts(self.course, is_cohorted=True)
        expected_response['available_division_schemes'] = [
            CourseDiscussionSettings.COHORT, CourseDiscussionSettings.ENROLLMENT_TRACK
        ]
        self._assert_current_settings(expected_response)

    def test_empty_body_patch_request(self):
        """Test the response status code on sending a PATCH request with an empty body or missing fields."""
        self._login_as_staff()
        response = self.patch_request("")
        assert response.status_code == 400

        response = self.patch_request({})
        assert response.status_code == 400

    @ddt.data(
        {'abc': 123},
        {'divided_course_wide_discussions': 3},
        {'divided_inline_discussions': 'a'},
        {'always_divide_inline_discussions': ['a']},
        {'division_scheme': True}
    )
    def test_invalid_body_parameters(self, body):
        """Test the response status code on sending a PATCH request with parameters having incorrect types."""
        self._login_as_staff()
        response = self.patch_request(body)
        assert response.status_code == 400

    def test_update_always_divide_inline_discussion_settings(self):
        """Test whether the 'always_divide_inline_discussions' setting is updated."""
        config_course_cohorts(self.course, is_cohorted=True)
        self._login_as_staff()
        expected_response = self._get_expected_response()
        self._assert_current_settings(expected_response)
        expected_response['always_divide_inline_discussions'] = True

        self._assert_patched_settings({'always_divide_inline_discussions': True}, expected_response)

    def test_update_course_wide_discussion_settings(self):
        """Test whether the 'divided_course_wide_discussions' setting is updated."""
        discussion_topics = {
            'Topic B': {'id': 'Topic B'}
        }
        config_course_cohorts(self.course, is_cohorted=True)
        config_course_discussions(self.course, discussion_topics=discussion_topics)
        expected_response = self._get_expected_response()
        self._login_as_staff()
        self._assert_current_settings(expected_response)
        expected_response['divided_course_wide_discussions'] = [
            topic_name_to_id(self.course, "Topic B")
        ]
        self._assert_patched_settings(
            {'divided_course_wide_discussions': [topic_name_to_id(self.course, "Topic B")]},
            expected_response
        )
        expected_response['divided_course_wide_discussions'] = []
        self._assert_patched_settings(
            {'divided_course_wide_discussions': []},
            expected_response
        )

    def test_update_inline_discussion_settings(self):
        """Test whether the 'divided_inline_discussions' setting is updated."""
        config_course_cohorts(self.course, is_cohorted=True)
        self._login_as_staff()
        expected_response = self._get_expected_response()
        self._assert_current_settings(expected_response)

        now = datetime.now()
        ItemFactory.create(
            parent_location=self.course.location,
            category='discussion',
            discussion_id='Topic_A',
            discussion_category='Chapter',
            discussion_target='Discussion',
            start=now
        )
        expected_response['divided_inline_discussions'] = ['Topic_A', ]
        self._assert_patched_settings({'divided_inline_discussions': ['Topic_A']}, expected_response)

        expected_response['divided_inline_discussions'] = []
        self._assert_patched_settings({'divided_inline_discussions': []}, expected_response)

    def test_update_division_scheme(self):
        """Test whether the 'division_scheme' setting is updated."""
        config_course_cohorts(self.course, is_cohorted=True)
        self._login_as_staff()
        expected_response = self._get_expected_response()
        self._assert_current_settings(expected_response)
        expected_response['division_scheme'] = 'none'
        self._assert_patched_settings({'division_scheme': 'none'}, expected_response)

    def test_update_reported_content_email_notifications(self):
        """Test whether the 'reported_content_email_notifications' setting is updated."""
        config_course_cohorts(self.course, is_cohorted=True)
        config_course_discussions(self.course, reported_content_email_notifications=True)
        expected_response = self._get_expected_response()
        expected_response['reported_content_email_notifications'] = True
        self._login_as_staff()
        self._assert_current_settings(expected_response)


@ddt.ddt
class CourseDiscussionRolesAPIViewTest(APITestCase, UrlResetMixin, ModuleStoreTestCase):
    """
    Test the course discussion roles management endpoint.
    """
    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(
            org="x",
            course="y",
            run="z",
            start=datetime.now(UTC),
        )
        self.password = 'edx'
        self.user = UserFactory(username='staff', password=self.password, is_staff=True)
        course_key = CourseKey.from_string('course-v1:x+y+z')
        seed_permissions_roles(course_key)

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def path(self, course_id=None, role=None):
        """Return the URL path to the endpoint based on the provided arguments."""
        course_id = str(self.course.id) if course_id is None else course_id
        role = 'Moderator' if role is None else role
        return reverse(
            'discussion_course_roles',
            kwargs={'course_id': course_id, 'rolename': role}
        )

    def _get_oauth_headers(self, user):
        """Return the OAuth headers for testing OAuth authentication."""
        access_token = AccessTokenFactory.create(user=user, application=ApplicationFactory()).token
        headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + access_token
        }
        return headers

    def _login_as_staff(self):
        """Log the client is as the staff user."""
        self.client.login(username=self.user.username, password=self.password)

    def _create_and_enroll_users(self, count):
        """Create 'count' number of users and enroll them in self.course."""
        users = []
        for _ in range(count):
            user = UserFactory()
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)
            users.append(user)
        return users

    def _add_users_to_role(self, users, rolename):
        """Add the given users to the given role."""
        role = Role.objects.get(name=rolename, course_id=self.course.id)
        for user in users:
            role.users.add(user)

    def post(self, role, user_id, action):
        """Make a POST request to the endpoint using the provided parameters."""
        self._login_as_staff()
        return self.client.post(self.path(role=role), {'user_id': user_id, 'action': action})

    @ddt.data('get', 'post')
    def test_authentication_required(self, method):
        """Test and verify that authentication is required for this endpoint."""
        self.client.logout()
        response = getattr(self.client, method)(self.path())
        assert response.status_code == 401

    def test_oauth(self):
        """Test that OAuth authentication works for this endpoint."""
        oauth_headers = self._get_oauth_headers(self.user)
        self.client.logout()
        response = self.client.get(self.path(), **oauth_headers)
        assert response.status_code == 200
        body = {'user_id': 'staff', 'action': 'allow'}
        response = self.client.post(self.path(), body, format='json', **oauth_headers)
        assert response.status_code == 200

    @ddt.data(
        {'username': 'u1', 'is_staff': False, 'expected_status': 403},
        {'username': 'u2', 'is_staff': True, 'expected_status': 200},
    )
    @ddt.unpack
    def test_staff_permission_required(self, username, is_staff, expected_status):
        """Test and verify that only users with staff permission can access this endpoint."""
        UserFactory(username=username, password='edx', is_staff=is_staff)
        self.client.login(username=username, password='edx')
        response = self.client.get(self.path())
        assert response.status_code == expected_status

        response = self.client.post(self.path(), {'user_id': username, 'action': 'allow'}, format='json')
        assert response.status_code == expected_status

    def test_non_existent_course_id(self):
        """Test the response when the endpoint URL contains a non-existent course id."""
        self._login_as_staff()
        path = self.path(course_id='course-v1:a+b+c')
        response = self.client.get(path)

        assert response.status_code == 404

        response = self.client.post(path)
        assert response.status_code == 404

    def test_non_existent_course_role(self):
        """Test the response when the endpoint URL contains a non-existent role."""
        self._login_as_staff()
        path = self.path(role='A')
        response = self.client.get(path)

        assert response.status_code == 400

        response = self.client.post(path)
        assert response.status_code == 400

    @ddt.data(
        {'role': 'Moderator', 'count': 0},
        {'role': 'Moderator', 'count': 1},
        {'role': 'Group Moderator', 'count': 2},
        {'role': 'Community TA', 'count': 3},
    )
    @ddt.unpack
    def test_get_role_members(self, role, count):
        """Test the get role members endpoint response."""
        config_course_cohorts(self.course, is_cohorted=True)
        users = self._create_and_enroll_users(count=count)

        self._add_users_to_role(users, role)
        self._login_as_staff()
        response = self.client.get(self.path(role=role))

        assert response.status_code == 200

        content = json.loads(response.content.decode('utf-8'))
        assert content['course_id'] == 'course-v1:x+y+z'
        assert len(content['results']) == count
        expected_fields = ('username', 'email', 'first_name', 'last_name', 'group_name')
        for item in content['results']:
            for expected_field in expected_fields:
                assert expected_field in item
        assert content['division_scheme'] == 'cohort'

    def test_post_missing_body(self):
        """Test the response with a POST request without a body."""
        self._login_as_staff()
        response = self.client.post(self.path())
        assert response.status_code == 400

    @ddt.data(
        {'a': 1},
        {'user_id': 'xyz', 'action': 'allow'},
        {'user_id': 'staff', 'action': 123},
    )
    def test_missing_or_invalid_parameters(self, body):
        """
        Test the response when the POST request has missing required parameters or
        invalid values for the required parameters.
        """
        self._login_as_staff()
        response = self.client.post(self.path(), body)
        assert response.status_code == 400

        response = self.client.post(self.path(), body, format='json')
        assert response.status_code == 400

    @ddt.data(
        {'action': 'allow', 'user_in_role': False},
        {'action': 'allow', 'user_in_role': True},
        {'action': 'revoke', 'user_in_role': False},
        {'action': 'revoke', 'user_in_role': True}
    )
    @ddt.unpack
    def test_post_update_user_role(self, action, user_in_role):
        """Test the response when updating the user's role"""
        users = self._create_and_enroll_users(count=1)
        user = users[0]
        role = 'Moderator'
        if user_in_role:
            self._add_users_to_role(users, role)

        response = self.post(role, user.username, action)
        assert response.status_code == 200
        content = json.loads(response.content.decode('utf-8'))
        assertion = self.assertTrue if action == 'allow' else self.assertFalse
        assertion(any(user.username in x['username'] for x in content['results']))


@ddt.ddt
@httpretty.activate
@override_waffle_flag(ENABLE_LEARNERS_STATS, True)
class CourseActivityStatsTest(ForumsEnableMixin, UrlResetMixin, CommentsServiceMockMixin, APITestCase,
                              SharedModuleStoreTestCase):
    """
    Tests for the course stats endpoint
    """

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self) -> None:
        super().setUp()
        self.course = CourseFactory.create()
        self.course_key = str(self.course.id)
        seed_permissions_roles(self.course.id)
        self.user = UserFactory(username='user')
        self.moderator = UserFactory(username='moderator')
        moderator_role = Role.objects.get(name="Moderator", course_id=self.course.id)
        moderator_role.users.add(self.moderator)
        self.stats = [
            {
                "active_flags": random.randint(0, 3),
                "inactive_flags": random.randint(0, 2),
                "replies": random.randint(0, 30),
                "responses": random.randint(0, 100),
                "threads": random.randint(0, 10),
                "username": f"user-{idx}"
            }
            for idx in range(10)
        ]

        for stat in self.stats:
            user = UserFactory.create(
                username=stat['username'],
                email=f"{stat['username']}@example.com",
                password='12345'
            )
            CourseEnrollment.enroll(user, self.course.id, mode='audit')

        CourseEnrollment.enroll(self.moderator, self.course.id, mode='audit')
        self.stats_without_flags = [{**stat, "active_flags": None, "inactive_flags": None} for stat in self.stats]
        self.register_course_stats_response(self.course_key, self.stats, 1, 3)
        self.url = reverse("discussion_course_activity_stats", kwargs={"course_key_string": self.course_key})

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def test_regular_user(self):
        """
        Tests that for a regular user stats are returned without flag counts
        """
        self.client.login(username=self.user.username, password='test')
        response = self.client.get(self.url)
        data = response.json()
        assert data["results"] == self.stats_without_flags

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def test_moderator_user(self):
        """
        Tests that for a moderator user stats are returned with flag counts
        """
        self.client.login(username=self.moderator.username, password='test')
        response = self.client.get(self.url)
        data = response.json()
        assert data["results"] == self.stats

    @ddt.data(
        ("moderator", "flagged", "flagged"),
        ("moderator", "activity", "activity"),
        ("moderator", "recency", "recency"),
        ("moderator", None, "flagged"),
        ("user", None, "activity"),
        ("user", "activity", "activity"),
        ("user", "recency", "recency"),
    )
    @ddt.unpack
    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def test_sorting(self, username, ordering_requested, ordering_performed):
        """
        Test valid sorting options and defaults
        """
        self.client.login(username=username, password='test')
        params = {}
        if ordering_requested:
            params = {"order_by": ordering_requested}
        self.client.get(self.url, params)
        assert urlparse(
            httpretty.last_request().path  # lint-amnesty, pylint: disable=no-member
        ).path == f"/api/v1/users/{self.course_key}/stats"
        assert parse_qs(
            urlparse(httpretty.last_request().path).query  # lint-amnesty, pylint: disable=no-member
        ).get("sort_key", None) == [ordering_performed]

    @ddt.data("flagged", "xyz")
    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def test_sorting_error_regular_user(self, order_by):
        """
        Test for invalid sorting options for regular users.
        """
        self.client.login(username=self.user.username, password='test')
        response = self.client.get(self.url, {"order_by": order_by})
        assert "order_by" in response.json()["field_errors"]

    @ddt.data(
        ('user', 'user-0,user-1,user-2,user-3,user-4,user-5,user-6,user-7,user-8,user-9'),
        ('moderator', 'moderator'),
    )
    @ddt.unpack
    @mock.patch.dict("django.conf.settings.FEATURES", {'ENABLE_DISCUSSION_SERVICE': True})
    def test_with_username_param(self, username_search_string, comma_separated_usernames):
        """
        Test for endpoint with username param.
        """
        params = {'username': username_search_string}
        self.client.login(username=self.moderator.username, password='test')
        self.client.get(self.url, params)
        assert urlparse(
            httpretty.last_request().path  # lint-amnesty, pylint: disable=no-member
        ).path == f'/api/v1/users/{self.course_key}/stats'
        assert parse_qs(
            urlparse(httpretty.last_request().path).query  # lint-amnesty, pylint: disable=no-member
        ).get('usernames', [None]) == [comma_separated_usernames]

    @mock.patch.dict("django.conf.settings.FEATURES", {'ENABLE_DISCUSSION_SERVICE': True})
    def test_with_username_param_with_no_matches(self):
        """
        Test for endpoint with username param with no matches.
        """
        params = {'username': 'unknown'}
        self.client.login(username=self.moderator.username, password='test')
        response = self.client.get(self.url, params)
        data = response.json()
        self.assertFalse(data['results'])
        assert data['pagination']['count'] == 0

    @ddt.data(
        'user-0',
        'USER-1',
        'User-2',
        'UsEr-3'
    )
    @mock.patch.dict("django.conf.settings.FEATURES", {'ENABLE_DISCUSSION_SERVICE': True})
    def test_with_username_param_case(self, username_search_string):
        """
        Test user search function is case-insensitive.
        """
        response = get_usernames_from_search_string(self.course_key, username_search_string, 1, 1)
        assert response == (username_search_string.lower(), 1, 1)
