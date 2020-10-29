"""
Tests for Discussion API views
"""


import json
from datetime import datetime

import ddt
import httpretty
import mock
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from rest_framework.parsers import JSONParser
from rest_framework.test import APIClient, APITestCase
from six import text_type
from six.moves import range
from six.moves.urllib.parse import urlparse

from common.test.utils import disable_signal
from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.discussion.django_comment_client.tests.utils import (
    ForumsEnableMixin,
    config_course_discussions,
    topic_name_to_id
)
from lms.djangoapps.discussion.rest_api import api
from lms.djangoapps.discussion.rest_api.tests.utils import (
    CommentsServiceMockMixin,
    ProfileImageTestMixin,
    make_minimal_cs_comment,
    make_minimal_cs_thread,
    make_paginated_api_response
)
from openedx.core.djangoapps.course_groups.tests.helpers import config_course_cohorts
from openedx.core.djangoapps.django_comment_common.models import CourseDiscussionSettings, Role
from openedx.core.djangoapps.django_comment_common.utils import seed_permissions_roles
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.djangoapps.oauth_dispatch.tests.factories import ApplicationFactory, AccessTokenFactory
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_storage
from openedx.core.djangoapps.user_api.models import RetirementState, UserRetirementStatus
from common.djangoapps.student.models import get_retired_username_by_username
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, SuperuserFactory, UserFactory
from common.djangoapps.util.testing import PatchMediaTypeMixin, UrlResetMixin
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls


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
        super(DiscussionAPIViewTestMixin, self).setUp()
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
        self.assertEqual(response.status_code, expected_status)
        parsed_content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(parsed_content, expected_content)

    def register_thread(self, overrides=None):
        """
        Create cs_thread with minimal fields and register response
        """
        cs_thread = make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": text_type(self.course.id),
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
            "course_id": text_type(self.course.id),
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
class CourseViewTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for CourseView"""
    def setUp(self):
        super(CourseViewTest, self).setUp()
        self.url = reverse("discussion_course", kwargs={"course_id": text_type(self.course.id)})

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
                "id": text_type(self.course.id),
                "blackouts": [],
                "thread_list_url": "http://testserver/api/discussion/v1/threads/?course_id=x%2Fy%2Fz",
                "following_thread_list_url": (
                    "http://testserver/api/discussion/v1/threads/?course_id=x%2Fy%2Fz&following=True"
                ),
                "topics_url": "http://testserver/api/discussion/v1/course_topics/x/y/z",
            }
        )


@httpretty.activate
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class RetireViewTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for CourseView"""
    def setUp(self):
        super(RetireViewTest, self).setUp()
        RetirementState.objects.create(state_name='PENDING', state_execution_order=1)
        self.retire_forums_state = RetirementState.objects.create(state_name='RETIRE_FORUMS', state_execution_order=11)

        self.retirement = UserRetirementStatus.create_retirement(self.user)
        self.retirement.current_state = self.retire_forums_state
        self.retirement.save()

        self.superuser = SuperuserFactory()
        self.retired_username = get_retired_username_by_username(self.user.username)
        self.url = reverse("retire_discussion_user")

    def assert_response_correct(self, response, expected_status, expected_content):
        """
        Assert that the response has the given status code and content
        """
        self.assertEqual(response.status_code, expected_status)

        if expected_content:
            self.assertEqual(response.content.decode('utf-8'), expected_content)

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
        response = self.client.post(self.url, data, **headers)
        self.assert_response_correct(response, 204, b"")

    def test_downstream_forums_error(self):
        """
        Check that we bubble up errors from the comments service
        """
        self.register_get_user_retire_response(self.user, status=500, body="Server error")
        headers = self.build_jwt_headers(self.superuser)
        data = {'username': self.user.username}
        response = self.client.post(self.url, data, **headers)
        self.assert_response_correct(response, 500, '"Server error"')

    def test_nonexistent_user(self):
        """
        Check that we handle unknown users appropriately
        """
        nonexistent_username = "nonexistent user"
        self.retired_username = get_retired_username_by_username(nonexistent_username)
        data = {'username': nonexistent_username}
        headers = self.build_jwt_headers(self.superuser)
        response = self.client.post(self.url, data, **headers)
        self.assert_response_correct(response, 404, None)

    def test_not_authenticated(self):
        """
        Override the parent implementation of this, we JWT auth for this API
        """
        pass


@ddt.ddt
@httpretty.activate
@mock.patch('django.conf.settings.USERNAME_REPLACEMENT_WORKER', 'test_replace_username_service_worker')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class ReplaceUsernamesViewTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for ReplaceUsernamesView"""
    def setUp(self):
        super(ReplaceUsernamesViewTest, self).setUp()
        self.client_user = UserFactory()
        self.client_user.username = "test_replace_username_service_worker"
        self.new_username = "test_username_replacement"
        self.url = reverse("replace_discussion_username")

    def assert_response_correct(self, response, expected_status, expected_content):
        """
        Assert that the response has the given status code and content
        """
        self.assertEqual(response.status_code, expected_status)

        if expected_content:
            self.assertEqual(text_type(response.content), expected_content)

    def build_jwt_headers(self, user):
        """
        Helper function for creating headers for the JWT authentication.
        """
        token = create_jwt_for_user(user)
        headers = {'HTTP_AUTHORIZATION': 'JWT ' + token}
        return headers

    def call_api(self, user, data):
        """ Helper function to call API with data """
        data = json.dumps(data)
        headers = self.build_jwt_headers(user)
        return self.client.post(self.url, data, content_type='application/json', **headers)

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
        response = self.call_api(self.client_user, data)
        self.assertEqual(response.status_code, 400)

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
        self.assertEqual(response.status_code, 401)

        # Test non-service worker
        random_user = UserFactory()
        response = self.call_api(random_user, data)
        self.assertEqual(response.status_code, 403)

        # Test service worker
        response = self.call_api(self.client_user, data)
        self.assertEqual(response.status_code, 200)

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
        response = self.call_api(self.client_user, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_response)

    def test_not_authenticated(self):
        """
        Override the parent implementation of this, we JWT auth for this API
        """
        pass


@ddt.ddt
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CourseTopicsViewTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """
    Tests for CourseTopicsView
    """
    def setUp(self):
        super(CourseTopicsViewTest, self).setUp()
        self.url = reverse("course_topics", kwargs={"course_id": text_type(self.course.id)})

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
        course_url = reverse("course_topics", kwargs={"course_id": text_type(course.id)})
        # add some discussion xblocks
        for i in range(modules_count):
            ItemFactory.create(
                parent_location=course.location,
                category='discussion',
                discussion_id='id_module_{}'.format(i),
                discussion_category='Category {}'.format(i),
                discussion_target='Discussion {}'.format(i),
                publish_item=False,
            )
        return course_url

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
                    "thread_list_url":
                        "http://testserver/api/discussion/v1/threads/?course_id=x%2Fy%2Fz&topic_id=test_topic",
                }],
            }
        )

    @ddt.data(
        (2, ModuleStoreEnum.Type.mongo, 2, {"Test Topic 1": {"id": "test_topic_1"}}),
        (2, ModuleStoreEnum.Type.mongo, 2,
         {"Test Topic 1": {"id": "test_topic_1"}, "Test Topic 2": {"id": "test_topic_2"}}),
        (2, ModuleStoreEnum.Type.split, 3, {"Test Topic 1": {"id": "test_topic_1"}}),
        (2, ModuleStoreEnum.Type.split, 3,
         {"Test Topic 1": {"id": "test_topic_1"}, "Test Topic 2": {"id": "test_topic_2"}}),
        (10, ModuleStoreEnum.Type.split, 3, {"Test Topic 1": {"id": "test_topic_1"}}),
    )
    @ddt.unpack
    def test_bulk_response(self, modules_count, module_store, mongo_calls, topics):
        course_url = self.create_course(modules_count, module_store, topics)
        with check_mongo_calls(mongo_calls):
            with modulestore().default_store(module_store):
                self.client.get(course_url)

    def test_discussion_topic_404(self):
        """
        Tests discussion topic does not exist for the given topic id.
        """
        topic_id = "courseware-topic-id"
        self.make_discussion_xblock(topic_id, "test_category", "test_target")
        url = "{}?topic_id=invalid_topic_id".format(self.url)
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
        url = "{}?topic_id=topic_id_1,topic_id_2".format(self.url)
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
                                               "course_id=x%2Fy%2Fz&topic_id=topic_id_1",
                            "name": "test_target_1"
                        }],
                        "id": None,
                        "thread_list_url": "http://testserver/api/discussion/v1/threads/?"
                                           "course_id=x%2Fy%2Fz&topic_id=topic_id_1",
                        "name": "test_category_1"
                    },
                    {
                        "children":
                            [{
                                "children": [],
                                "id": "topic_id_2",
                                "thread_list_url": "http://testserver/api/discussion/v1/threads/?"
                                                   "course_id=x%2Fy%2Fz&topic_id=topic_id_2",
                                "name": "test_target_2"
                            }],
                        "id": None,
                        "thread_list_url": "http://testserver/api/discussion/v1/threads/?"
                                           "course_id=x%2Fy%2Fz&topic_id=topic_id_2",
                        "name": "test_category_2"
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
        super(ThreadViewSetListTest, self).setUp()
        self.author = UserFactory.create()
        self.url = reverse("thread-list")

    def create_source_thread(self, overrides=None):
        """
        Create a sample source cs_thread
        """
        thread = make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": text_type(self.course.id),
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
        response = self.client.get(self.url, {"course_id": text_type("non/existent/course")})
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
            "unread_comment_count": 3,
            "voted": True,
            "author": self.author.username,
            "editable_fields": ["abuse_flagged", "following", "read", "voted"],
        })]
        self.register_get_threads_response(source_threads, page=1, num_pages=2)
        response = self.client.get(self.url, {"course_id": text_type(self.course.id), "following": ""})
        expected_response = make_paginated_api_response(
            results=expected_threads,
            count=1,
            num_pages=2,
            next_link="http://testserver/api/discussion/v1/threads/?course_id=x%2Fy%2Fz&following=&page=2",
            previous_link=None
        )
        expected_response.update({"text_search_rewrite": None})
        self.assert_response_correct(
            response,
            200,
            expected_response
        )
        self.assert_last_query_params({
            "user_id": [text_type(self.user.id)],
            "course_id": [text_type(self.course.id)],
            "sort_key": ["activity"],
            "page": ["1"],
            "per_page": ["10"],
        })

    @ddt.data("unread", "unanswered")
    def test_view_query(self, query):
        threads = [make_minimal_cs_thread()]
        self.register_get_user_response(self.user)
        self.register_get_threads_response(threads, page=1, num_pages=1)
        self.client.get(
            self.url,
            {
                "course_id": text_type(self.course.id),
                "view": query,
            }
        )
        self.assert_last_query_params({
            "user_id": [text_type(self.user.id)],
            "course_id": [text_type(self.course.id)],
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
            {"course_id": text_type(self.course.id), "page": "18", "page_size": "4"}
        )
        self.assert_response_correct(
            response,
            404,
            {"developer_message": "Page not found (No results on this page)."}
        )
        self.assert_last_query_params({
            "user_id": [text_type(self.user.id)],
            "course_id": [text_type(self.course.id)],
            "sort_key": ["activity"],
            "page": ["18"],
            "per_page": ["4"],
        })

    def test_text_search(self):
        self.register_get_user_response(self.user)
        self.register_get_threads_search_response([], None, num_pages=0)
        response = self.client.get(
            self.url,
            {"course_id": text_type(self.course.id), "text_search": "test search string"}
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
            "user_id": [text_type(self.user.id)],
            "course_id": [text_type(self.course.id)],
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
                "course_id": text_type(self.course.id),
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
        self.assertEqual(
            urlparse(httpretty.last_request().path).path,
            "/api/v1/users/{}/subscribed_threads".format(self.user.id)
        )

    @ddt.data(False, "false", "0")
    def test_following_false(self, following):
        response = self.client.get(
            self.url,
            {
                "course_id": text_type(self.course.id),
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
                "course_id": text_type(self.course.id),
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
                "course_id": text_type(self.course.id),
                "order_by": http_query,
            }
        )
        self.assert_last_query_params({
            "user_id": [text_type(self.user.id)],
            "course_id": [text_type(self.course.id)],
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
                "course_id": text_type(self.course.id),
                "order_direction": "desc",
            }
        )
        self.assert_last_query_params({
            "user_id": [text_type(self.user.id)],
            "course_id": [text_type(self.course.id)],
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
            "course_id": text_type(self.course.id),
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
            {"course_id": text_type(self.course.id), "requested_fields": "profile_image"},
        )
        self.assertEqual(response.status_code, 200)
        response_threads = json.loads(response.content.decode('utf-8'))['results']

        for response_thread in response_threads:
            expected_profile_data = self.get_expected_user_profile(response_thread['author'])
            response_users = response_thread['users']
            self.assertEqual(expected_profile_data, response_users[response_thread['author']])

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
            {"course_id": text_type(self.course.id), "requested_fields": "profile_image"},
        )
        self.assertEqual(response.status_code, 200)
        response_thread = json.loads(response.content.decode('utf-8'))['results'][0]
        self.assertIsNone(response_thread['author'])
        self.assertEqual({}, response_thread['users'])


@httpretty.activate
@disable_signal(api, 'thread_created')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class ThreadViewSetCreateTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for ThreadViewSet create"""
    def setUp(self):
        super(ThreadViewSetCreateTest, self).setUp()
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
            "course_id": text_type(self.course.id),
            "topic_id": "test_topic",
            "type": "discussion",
            "title": "Test Title",
            "raw_body": "Test body",
        }
        response = self.client.post(
            self.url,
            json.dumps(request_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_data, self.expected_thread_data({"read": True}))
        self.assertEqual(
            httpretty.last_request().parsed_body,
            {
                "course_id": [text_type(self.course.id)],
                "commentable_id": ["test_topic"],
                "thread_type": ["discussion"],
                "title": ["Test Title"],
                "body": ["Test body"],
                "user_id": [str(self.user.id)],
            }
        )

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
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_data, expected_response_data)


@ddt.ddt
@httpretty.activate
@disable_signal(api, 'thread_edited')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class ThreadViewSetPartialUpdateTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase, PatchMediaTypeMixin):
    """Tests for ThreadViewSet partial_update"""
    def setUp(self):
        self.unsupported_media_type = JSONParser.media_type
        super(ThreadViewSetPartialUpdateTest, self).setUp()
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
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            response_data,
            self.expected_thread_data({
                "raw_body": "Edited body",
                "rendered_body": "<p>Edited body</p>",
                "editable_fields": [
                    "abuse_flagged", "following", "raw_body", "read", "title", "topic_id", "type", "voted"
                ],
                "created_at": "Test Created Date",
                "updated_at": "Test Updated Date",
                "comment_count": 1,
                "read": True,
                "response_count": 2,
            })
        )
        self.assertEqual(
            httpretty.last_request().parsed_body,
            {
                "course_id": [text_type(self.course.id)],
                "commentable_id": ["test_topic"],
                "thread_type": ["discussion"],
                "title": ["Test Title"],
                "body": ["Edited body"],
                "user_id": [str(self.user.id)],
                "anonymous": ["False"],
                "anonymous_to_peers": ["False"],
                "closed": ["False"],
                "pinned": ["False"],
                "read": ["True"],
            }
        )

    def test_error(self):
        self.register_get_user_response(self.user)
        self.register_thread()
        request_data = {"title": ""}
        response = self.request_patch(request_data)
        expected_response_data = {
            "field_errors": {"title": {"developer_message": "This field may not be blank."}}
        }
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_data, expected_response_data)

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
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            response_data,
            self.expected_thread_data({
                "read": True,
                "closed": True,
                "abuse_flagged": value,
                "editable_fields": ["abuse_flagged", "read"],
                "comment_count": 1,
                "unread_comment_count": 0,
            })
        )

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
        self.assertEqual(response.status_code, 400)

    def test_patch_read_owner_user(self):
        self.register_get_user_response(self.user)
        self.register_thread({"resp_total": 2})
        self.register_read_response(self.user, "thread", "test_thread")
        request_data = {"read": True}

        response = self.request_patch(request_data)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            response_data,
            self.expected_thread_data({
                "comment_count": 1,
                "read": True,
                "editable_fields": [
                    "abuse_flagged", "following", "raw_body", "read", "title", "topic_id", "type", "voted"
                ],
                "response_count": 2,
            })
        )

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
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            response_data,
            self.expected_thread_data({
                "author": str(thread_owner_user.username),
                "comment_count": 1,
                "read": True,
                "editable_fields": [
                    "abuse_flagged", "following", "read", "voted"
                ],
                "response_count": 2,
            })
        )


@httpretty.activate
@disable_signal(api, 'thread_deleted')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class ThreadViewSetDeleteTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for ThreadViewSet delete"""
    def setUp(self):
        super(ThreadViewSetDeleteTest, self).setUp()
        self.url = reverse("thread-detail", kwargs={"thread_id": "test_thread"})
        self.thread_id = "test_thread"

    def test_basic(self):
        self.register_get_user_response(self.user)
        cs_thread = make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": text_type(self.course.id),
            "username": self.user.username,
            "user_id": str(self.user.id),
        })
        self.register_get_thread_response(cs_thread)
        self.register_delete_thread_response(self.thread_id)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertEqual(
            urlparse(httpretty.last_request().path).path,
            "/api/v1/threads/{}".format(self.thread_id)
        )
        self.assertEqual(httpretty.last_request().method, "DELETE")

    def test_delete_nonexistent_thread(self):
        self.register_get_thread_error_response(self.thread_id, 404)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 404)


@ddt.ddt
@httpretty.activate
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CommentViewSetListTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase, ProfileImageTestMixin):
    """Tests for CommentViewSet list"""
    def setUp(self):
        super(CommentViewSetListTest, self).setUp()
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
        overrides.setdefault("course_id", text_type(self.course.id))
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
            "voted": False,
            "vote_count": 0,
            "children": [],
            "editable_fields": ["abuse_flagged", "voted"],
            "child_count": 0,
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
            "rendered_body": "<p>Test body</p>",
            "created_at": "2015-05-11T00:00:00Z",
            "updated_at": "2015-05-11T11:11:11Z",
        })]
        self.register_get_thread_response({
            "id": self.thread_id,
            "course_id": text_type(self.course.id),
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
            "course_id": text_type(self.course.id),
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
        self.assertEqual(parsed_content["results"][0]["id"], comment_id)

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
            "course_id": text_type(self.course.id),
            "thread_type": "discussion",
            "children": [response_1, response_2],
            "resp_total": 2,
            "comments_count": 8,
            "unread_comments_count": 0,

        })
        self.register_get_thread_response(thread)
        response = self.client.get(self.url, {"thread_id": self.thread_id})
        expected_comments = [
            self.expected_response_comment(overrides={"id": "test_response_1", "child_count": 2}),
            self.expected_response_comment(overrides={"id": "test_response_2", "child_count": 3}),
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
            "course_id": text_type(self.course.id),
            "thread_type": "discussion",
            "children": source_comments,
            "resp_total": 100,
        })
        self.register_get_user_response(self.user, upvoted_ids=["test_comment"])
        self.create_profile_image(self.user, get_profile_image_storage())

        response = self.client.get(self.url, {"thread_id": self.thread_id, "requested_fields": "profile_image"})
        self.assertEqual(response.status_code, 200)
        response_comments = json.loads(response.content.decode('utf-8'))['results']
        for response_comment in response_comments:
            expected_profile_data = self.get_expected_user_profile(response_comment['author'])
            response_users = response_comment['users']
            self.assertEqual(expected_profile_data, response_users[response_comment['author']])

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
        self.assertEqual(response.status_code, 200)
        response_comments = json.loads(response.content.decode('utf-8'))['results']
        for response_comment in response_comments:
            expected_author_profile_data = self.get_expected_user_profile(response_comment['author'])
            expected_endorser_profile_data = self.get_expected_user_profile(response_comment['endorsed_by'])
            response_users = response_comment['users']
            self.assertEqual(expected_author_profile_data, response_users[response_comment['author']])
            self.assertEqual(expected_endorser_profile_data, response_users[response_comment['endorsed_by']])

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
        self.assertEqual(response.status_code, 200)
        response_comments = json.loads(response.content.decode('utf-8'))['results']
        for response_comment in response_comments:
            expected_author_profile_data = self.get_expected_user_profile(response_comment['author'])
            response_users = response_comment['users']
            self.assertEqual(expected_author_profile_data, response_users[response_comment['author']])
            self.assertNotIn(response_comment['endorsed_by'], response_users)


@httpretty.activate
@disable_signal(api, 'comment_deleted')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CommentViewSetDeleteTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for ThreadViewSet delete"""

    def setUp(self):
        super(CommentViewSetDeleteTest, self).setUp()
        self.url = reverse("comment-detail", kwargs={"comment_id": "test_comment"})
        self.comment_id = "test_comment"

    def test_basic(self):
        self.register_get_user_response(self.user)
        cs_thread = make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": text_type(self.course.id),
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
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertEqual(
            urlparse(httpretty.last_request().path).path,
            "/api/v1/comments/{}".format(self.comment_id)
        )
        self.assertEqual(httpretty.last_request().method, "DELETE")

    def test_delete_nonexistent_comment(self):
        self.register_get_comment_error_response(self.comment_id, 404)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 404)


@httpretty.activate
@disable_signal(api, 'comment_created')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CommentViewSetCreateTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for CommentViewSet create"""
    def setUp(self):
        super(CommentViewSetCreateTest, self).setUp()
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
            "voted": False,
            "vote_count": 0,
            "children": [],
            "editable_fields": ["abuse_flagged", "raw_body", "voted"],
            "child_count": 0,
        }
        response = self.client.post(
            self.url,
            json.dumps(request_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_data, expected_response_data)
        self.assertEqual(
            urlparse(httpretty.last_request().path).path,
            "/api/v1/threads/test_thread/comments"
        )
        self.assertEqual(
            httpretty.last_request().parsed_body,
            {
                "course_id": [text_type(self.course.id)],
                "body": ["Test body"],
                "user_id": [str(self.user.id)],
            }
        )

    def test_error(self):
        response = self.client.post(
            self.url,
            json.dumps({}),
            content_type="application/json"
        )
        expected_response_data = {
            "field_errors": {"thread_id": {"developer_message": "This field is required."}}
        }
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_data, expected_response_data)

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
        self.assertEqual(response.status_code, 403)


@ddt.ddt
@disable_signal(api, 'comment_edited')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CommentViewSetPartialUpdateTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase, PatchMediaTypeMixin):
    """Tests for CommentViewSet partial_update"""
    def setUp(self):
        self.unsupported_media_type = JSONParser.media_type
        super(CommentViewSetPartialUpdateTest, self).setUp()
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
            "voted": False,
            "vote_count": 0,
            "children": [],
            "editable_fields": [],
            "child_count": 0,
        }
        response_data.update(overrides or {})
        return response_data

    def test_basic(self):
        self.register_thread()
        self.register_comment({"created_at": "Test Created Date", "updated_at": "Test Updated Date"})
        request_data = {"raw_body": "Edited body"}
        response = self.request_patch(request_data)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            response_data,
            self.expected_response_data({
                "raw_body": "Edited body",
                "rendered_body": "<p>Edited body</p>",
                "editable_fields": ["abuse_flagged", "raw_body", "voted"],
                "created_at": "Test Created Date",
                "updated_at": "Test Updated Date",
            })
        )
        self.assertEqual(
            httpretty.last_request().parsed_body,
            {
                "body": ["Edited body"],
                "course_id": [text_type(self.course.id)],
                "user_id": [str(self.user.id)],
                "anonymous": ["False"],
                "anonymous_to_peers": ["False"],
                "endorsed": ["False"],
            }
        )

    def test_error(self):
        self.register_thread()
        self.register_comment()
        request_data = {"raw_body": ""}
        response = self.request_patch(request_data)
        expected_response_data = {
            "field_errors": {"raw_body": {"developer_message": "This field may not be blank."}}
        }
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response_data, expected_response_data)

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
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            response_data,
            self.expected_response_data({
                "abuse_flagged": value,
                "editable_fields": ["abuse_flagged"],
            })
        )

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
        self.assertEqual(response.status_code, 400)


@httpretty.activate
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class ThreadViewSetRetrieveTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase, ProfileImageTestMixin):
    """Tests for ThreadViewSet Retrieve"""
    def setUp(self):
        super(ThreadViewSetRetrieveTest, self).setUp()
        self.url = reverse("thread-detail", kwargs={"thread_id": "test_thread"})
        self.thread_id = "test_thread"

    def test_basic(self):
        self.register_get_user_response(self.user)
        cs_thread = make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": text_type(self.course.id),
            "commentable_id": "test_topic",
            "username": self.user.username,
            "user_id": str(self.user.id),
            "title": "Test Title",
            "body": "Test body",
        })
        self.register_get_thread_response(cs_thread)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content.decode('utf-8')),
            self.expected_thread_data({"unread_comment_count": 1})
        )
        self.assertEqual(httpretty.last_request().method, "GET")

    def test_retrieve_nonexistent_thread(self):
        self.register_get_thread_error_response(self.thread_id, 404)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_profile_image_requested_field(self):
        """
        Tests thread has user profile image details if called in requested_fields
        """
        self.register_get_user_response(self.user)
        cs_thread = make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": text_type(self.course.id),
            "username": self.user.username,
            "user_id": str(self.user.id),
        })
        self.register_get_thread_response(cs_thread)
        self.create_profile_image(self.user, get_profile_image_storage())
        response = self.client.get(self.url, {"requested_fields": "profile_image"})
        self.assertEqual(response.status_code, 200)
        expected_profile_data = self.get_expected_user_profile(self.user.username)
        response_users = json.loads(response.content.decode('utf-8'))['users']
        self.assertEqual(expected_profile_data, response_users[self.user.username])


@httpretty.activate
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CommentViewSetRetrieveTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase, ProfileImageTestMixin):
    """Tests for CommentViewSet Retrieve"""
    def setUp(self):
        super(CommentViewSetRetrieveTest, self).setUp()
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
            "course_id": text_type(self.course.id),
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
            "course_id": text_type(self.course.id),
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
            "editable_fields": ["abuse_flagged", "raw_body", "voted"],
            "child_count": 0,
        }

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content.decode('utf-8'))['results'][0], expected_response_data)

    def test_retrieve_nonexistent_comment(self):
        self.register_get_comment_error_response(self.comment_id, 404)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

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
            "course_id": text_type(self.course.id),
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
            'course_id': text_type(self.course.id),
            'children': [cs_comment],
        })
        self.register_get_thread_response(cs_thread)
        self.register_get_comment_response(cs_comment)
        self.create_profile_image(self.user, get_profile_image_storage())

        response = self.client.get(self.url, {'requested_fields': 'profile_image'})
        self.assertEqual(response.status_code, 200)
        response_comments = json.loads(response.content.decode('utf-8'))['results']

        for response_comment in response_comments:
            expected_profile_data = self.get_expected_user_profile(response_comment['author'])
            response_users = response_comment['users']
            self.assertEqual(expected_profile_data, response_users[response_comment['author']])


@ddt.ddt
class CourseDiscussionSettingsAPIViewTest(APITestCase, UrlResetMixin, ModuleStoreTestCase):
    """
    Test the course discussion settings handler API endpoint.
    """
    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(CourseDiscussionSettingsAPIViewTest, self).setUp()
        self.course = CourseFactory.create(
            org="x",
            course="y",
            run="z",
            start=datetime.now(UTC),
            discussion_topics={"Test Topic": {"id": "test_topic"}}
        )
        self.path = reverse('discussion_course_settings', kwargs={'course_id': text_type(self.course.id)})
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

    def _create_divided_discussions(self):
        """Create some divided discussions for testing."""
        divided_inline_discussions = ['Topic A', ]
        divided_course_wide_discussions = ['Topic B', ]
        divided_discussions = divided_inline_discussions + divided_course_wide_discussions

        ItemFactory.create(
            parent_location=self.course.location,
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
            u'always_divide_inline_discussions': False,
            u'divided_inline_discussions': [],
            u'divided_course_wide_discussions': [],
            u'id': 1,
            u'division_scheme': u'cohort',
            u'available_division_schemes': [u'cohort']
        }

    def patch_request(self, data, headers=None):
        headers = headers if headers else {}
        return self.client.patch(self.path, json.dumps(data), content_type='application/merge-patch+json', **headers)

    def _assert_current_settings(self, expected_response):
        """Validate the current discussion settings against the expected response."""
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content, expected_response)

    def _assert_patched_settings(self, data, expected_response):
        """Validate the patched settings against the expected response."""
        response = self.patch_request(data)
        self.assertEqual(response.status_code, 204)
        self._assert_current_settings(expected_response)

    @ddt.data('get', 'patch')
    def test_authentication_required(self, method):
        """Test and verify that authentication is required for this endpoint."""
        self.client.logout()
        response = getattr(self.client, method)(self.path)
        self.assertEqual(response.status_code, 401)

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
        self.assertEqual(response.status_code, get_status)

        response = self.patch_request(
            {'always_divide_inline_discussions': True}, headers
        )
        self.assertEqual(response.status_code, put_status)

    def test_non_existent_course_id(self):
        """Test the response when this endpoint is passed a non-existent course id."""
        self._login_as_staff()
        response = self.client.get(
            reverse('discussion_course_settings', kwargs={
                'course_id': 'a/b/c'
            })
        )
        self.assertEqual(response.status_code, 404)

    def test_get_settings(self):
        """Test the current discussion settings against the expected response."""
        divided_inline_discussions, divided_course_wide_discussions = self._create_divided_discussions()
        self._login_as_staff()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        expected_response = self._get_expected_response()
        expected_response['divided_course_wide_discussions'] = [
            topic_name_to_id(self.course, name) for name in divided_course_wide_discussions
        ]
        expected_response['divided_inline_discussions'] = [
            topic_name_to_id(self.course, name) for name in divided_inline_discussions
        ]
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content, expected_response)

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
        self.assertEqual(response.status_code, 400)

        response = self.patch_request({})
        self.assertEqual(response.status_code, 400)

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
        self.assertEqual(response.status_code, 400)

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


@ddt.ddt
class CourseDiscussionRolesAPIViewTest(APITestCase, UrlResetMixin, ModuleStoreTestCase):
    """
    Test the course discussion roles management endpoint.
    """
    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(CourseDiscussionRolesAPIViewTest, self).setUp()
        self.course = CourseFactory.create(
            org="x",
            course="y",
            run="z",
            start=datetime.now(UTC),
        )
        self.password = 'edx'
        self.user = UserFactory(username='staff', password=self.password, is_staff=True)
        course_key = CourseKey.from_string('x/y/z')
        seed_permissions_roles(course_key)

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def path(self, course_id=None, role=None):
        """Return the URL path to the endpoint based on the provided arguments."""
        course_id = text_type(self.course.id) if course_id is None else course_id
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
        self.assertEqual(response.status_code, 401)

    def test_oauth(self):
        """Test that OAuth authentication works for this endpoint."""
        oauth_headers = self._get_oauth_headers(self.user)
        self.client.logout()
        response = self.client.get(self.path(), **oauth_headers)
        self.assertEqual(response.status_code, 200)
        body = {'user_id': 'staff', 'action': 'allow'}
        response = self.client.post(self.path(), body, format='json', **oauth_headers)
        self.assertEqual(response.status_code, 200)

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
        self.assertEqual(response.status_code, expected_status)

        response = self.client.post(self.path(), {'user_id': username, 'action': 'allow'}, format='json')
        self.assertEqual(response.status_code, expected_status)

    def test_non_existent_course_id(self):
        """Test the response when the endpoint URL contains a non-existent course id."""
        self._login_as_staff()
        path = self.path(course_id='a/b/c')
        response = self.client.get(path)

        self.assertEqual(response.status_code, 404)

        response = self.client.post(path)
        self.assertEqual(response.status_code, 404)

    def test_non_existent_course_role(self):
        """Test the response when the endpoint URL contains a non-existent role."""
        self._login_as_staff()
        path = self.path(role='A')
        response = self.client.get(path)

        self.assertEqual(response.status_code, 400)

        response = self.client.post(path)
        self.assertEqual(response.status_code, 400)

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

        self.assertEqual(response.status_code, 200)

        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content['course_id'], 'x/y/z')
        self.assertEqual(len(content['results']), count)
        expected_fields = ('username', 'email', 'first_name', 'last_name', 'group_name')
        for item in content['results']:
            for expected_field in expected_fields:
                self.assertIn(expected_field, item)
        self.assertEqual(content['division_scheme'], 'cohort')

    def test_post_missing_body(self):
        """Test the response with a POST request without a body."""
        self._login_as_staff()
        response = self.client.post(self.path())
        self.assertEqual(response.status_code, 400)

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
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.path(), body, format='json')
        self.assertEqual(response.status_code, 400)

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
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode('utf-8'))
        assertion = self.assertTrue if action == 'allow' else self.assertFalse
        assertion(any(user.username in x['username'] for x in content['results']))
