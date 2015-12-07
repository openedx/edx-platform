"""
Tests for Discussion API views
"""
from datetime import datetime
import json
from urlparse import urlparse

import ddt
import httpretty
import mock
from pytz import UTC

from django.core.urlresolvers import reverse
from rest_framework.parsers import JSONParser

from rest_framework.test import APIClient
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore

from common.test.utils import disable_signal
from discussion_api import api
from discussion_api.tests.utils import (
    CommentsServiceMockMixin,
    make_minimal_cs_comment,
    make_minimal_cs_thread,
)
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from util.testing import UrlResetMixin, PatchMediaTypeMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, check_mongo_calls, ItemFactory


class DiscussionAPIViewTestMixin(CommentsServiceMockMixin, UrlResetMixin):
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
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.client.login(username=self.user.username, password=self.password)

    def assert_response_correct(self, response, expected_status, expected_content):
        """
        Assert that the response has the given status code and parsed content
        """
        self.assertEqual(response.status_code, expected_status)
        parsed_content = json.loads(response.content)
        self.assertEqual(parsed_content, expected_content)

    def register_thread(self, overrides=None):
        """
        Create cs_thread with minimal fields and register response
        """
        cs_thread = make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": unicode(self.course.id),
            "commentable_id": "original_topic",
            "username": self.user.username,
            "user_id": str(self.user.id),
            "thread_type": "discussion",
            "title": "Original Title",
            "body": "Original body",
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
            "course_id": unicode(self.course.id),
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
        self.url = reverse("discussion_course", kwargs={"course_id": unicode(self.course.id)})

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
                "id": unicode(self.course.id),
                "blackouts": [],
                "thread_list_url": "http://testserver/api/discussion/v1/threads/?course_id=x%2Fy%2Fz",
                "following_thread_list_url": (
                    "http://testserver/api/discussion/v1/threads/?course_id=x%2Fy%2Fz&following=True"
                ),
                "topics_url": "http://testserver/api/discussion/v1/course_topics/x/y/z",
            }
        )


@ddt.ddt
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CourseTopicsViewTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for CourseTopicsView"""
    def setUp(self):
        super(CourseTopicsViewTest, self).setUp()
        self.url = reverse("course_topics", kwargs={"course_id": unicode(self.course.id)})

    def create_course(self, modules_count, module_store, topics):
        """
        Create a course in a specified module store with discussion module and topics
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
        course_url = reverse("course_topics", kwargs={"course_id": unicode(course.id)})
        # add some discussion modules
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


@ddt.ddt
@httpretty.activate
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class ThreadViewSetListTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for ThreadViewSet list"""
    def setUp(self):
        super(ThreadViewSetListTest, self).setUp()
        self.author = UserFactory.create()
        self.url = reverse("thread-list")

    def test_course_id_missing(self):
        response = self.client.get(self.url)
        self.assert_response_correct(
            response,
            400,
            {"field_errors": {"course_id": {"developer_message": "This field is required."}}}
        )

    def test_404(self):
        response = self.client.get(self.url, {"course_id": unicode("non/existent/course")})
        self.assert_response_correct(
            response,
            404,
            {"developer_message": "Course not found."}
        )

    def test_basic(self):
        self.register_get_user_response(self.user, upvoted_ids=["test_thread"])
        source_threads = [{
            "type": "thread",
            "id": "test_thread",
            "course_id": unicode(self.course.id),
            "commentable_id": "test_topic",
            "group_id": None,
            "user_id": str(self.author.id),
            "username": self.author.username,
            "anonymous": False,
            "anonymous_to_peers": False,
            "created_at": "2015-04-28T00:00:00Z",
            "updated_at": "2015-04-28T11:11:11Z",
            "thread_type": "discussion",
            "title": "Test Title",
            "body": "Test body",
            "pinned": False,
            "closed": False,
            "abuse_flaggers": [],
            "votes": {"up_count": 4},
            "comments_count": 5,
            "unread_comments_count": 3,
            "read": False,
            "endorsed": False
        }]
        expected_threads = [{
            "id": "test_thread",
            "course_id": unicode(self.course.id),
            "topic_id": "test_topic",
            "group_id": None,
            "group_name": None,
            "author": self.author.username,
            "author_label": None,
            "created_at": "2015-04-28T00:00:00Z",
            "updated_at": "2015-04-28T11:11:11Z",
            "type": "discussion",
            "title": "Test Title",
            "raw_body": "Test body",
            "rendered_body": "<p>Test body</p>",
            "pinned": False,
            "closed": False,
            "following": False,
            "abuse_flagged": False,
            "voted": True,
            "vote_count": 4,
            "comment_count": 6,
            "unread_comment_count": 4,
            "comment_list_url": "http://testserver/api/discussion/v1/comments/?thread_id=test_thread",
            "endorsed_comment_list_url": None,
            "non_endorsed_comment_list_url": None,
            "editable_fields": ["abuse_flagged", "following", "read", "voted"],
            "read": False,
            "has_endorsed": False,
        }]
        self.register_get_threads_response(source_threads, page=1, num_pages=2)
        response = self.client.get(self.url, {"course_id": unicode(self.course.id), "following": ""})
        self.assert_response_correct(
            response,
            200,
            {
                "results": expected_threads,
                "next": "http://testserver/api/discussion/v1/threads/?course_id=x%2Fy%2Fz&page=2",
                "previous": None,
                "text_search_rewrite": None,
            }
        )
        self.assert_last_query_params({
            "user_id": [unicode(self.user.id)],
            "course_id": [unicode(self.course.id)],
            "sort_key": ["activity"],
            "sort_order": ["desc"],
            "page": ["1"],
            "per_page": ["10"],
            "recursive": ["False"],
        })

    @ddt.data("unread", "unanswered")
    def test_view_query(self, query):
        threads = [make_minimal_cs_thread()]
        self.register_get_user_response(self.user)
        self.register_get_threads_response(threads, page=1, num_pages=1)
        self.client.get(
            self.url,
            {
                "course_id": unicode(self.course.id),
                "view": query,
            }
        )
        self.assert_last_query_params({
            "user_id": [unicode(self.user.id)],
            "course_id": [unicode(self.course.id)],
            "sort_key": ["activity"],
            "sort_order": ["desc"],
            "recursive": ["False"],
            "page": ["1"],
            "per_page": ["10"],
            query: ["true"],
        })

    def test_pagination(self):
        self.register_get_user_response(self.user)
        self.register_get_threads_response([], page=1, num_pages=1)
        response = self.client.get(
            self.url,
            {"course_id": unicode(self.course.id), "page": "18", "page_size": "4"}
        )
        self.assert_response_correct(
            response,
            404,
            {"developer_message": "Not found."}
        )
        self.assert_last_query_params({
            "user_id": [unicode(self.user.id)],
            "course_id": [unicode(self.course.id)],
            "sort_key": ["activity"],
            "sort_order": ["desc"],
            "page": ["18"],
            "per_page": ["4"],
            "recursive": ["False"],
        })

    def test_text_search(self):
        self.register_get_user_response(self.user)
        self.register_get_threads_search_response([], None)
        response = self.client.get(
            self.url,
            {"course_id": unicode(self.course.id), "text_search": "test search string"}
        )
        self.assert_response_correct(
            response,
            200,
            {"results": [], "next": None, "previous": None, "text_search_rewrite": None}
        )
        self.assert_last_query_params({
            "user_id": [unicode(self.user.id)],
            "course_id": [unicode(self.course.id)],
            "sort_key": ["activity"],
            "sort_order": ["desc"],
            "page": ["1"],
            "per_page": ["10"],
            "recursive": ["False"],
            "text": ["test search string"],
        })

    @ddt.data(True, "true", "1")
    def test_following_true(self, following):
        self.register_get_user_response(self.user)
        self.register_subscribed_threads_response(self.user, [], page=1, num_pages=1)
        response = self.client.get(
            self.url,
            {
                "course_id": unicode(self.course.id),
                "following": following,
            }
        )
        self.assert_response_correct(
            response,
            200,
            {"results": [], "next": None, "previous": None, "text_search_rewrite": None}
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
                "course_id": unicode(self.course.id),
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
                "course_id": unicode(self.course.id),
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
                "course_id": unicode(self.course.id),
                "order_by": http_query,
            }
        )
        self.assert_last_query_params({
            "user_id": [unicode(self.user.id)],
            "course_id": [unicode(self.course.id)],
            "sort_order": ["desc"],
            "recursive": ["False"],
            "page": ["1"],
            "per_page": ["10"],
            "sort_key": [cc_query],
        })

    @ddt.data("asc", "desc")
    def test_order_direction(self, query):
        threads = [make_minimal_cs_thread()]
        self.register_get_user_response(self.user)
        self.register_get_threads_response(threads, page=1, num_pages=1)
        self.client.get(
            self.url,
            {
                "course_id": unicode(self.course.id),
                "order_direction": query,
            }
        )
        self.assert_last_query_params({
            "user_id": [unicode(self.user.id)],
            "course_id": [unicode(self.course.id)],
            "sort_key": ["activity"],
            "recursive": ["False"],
            "page": ["1"],
            "per_page": ["10"],
            "sort_order": [query],
        })


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
            "created_at": "2015-05-19T00:00:00Z",
            "updated_at": "2015-05-19T00:00:00Z",
        })
        self.register_post_thread_response(cs_thread)
        request_data = {
            "course_id": unicode(self.course.id),
            "topic_id": "test_topic",
            "type": "discussion",
            "title": "Test Title",
            "raw_body": "Test body",
        }
        expected_response_data = {
            "id": "test_thread",
            "course_id": unicode(self.course.id),
            "topic_id": "test_topic",
            "group_id": None,
            "group_name": None,
            "author": self.user.username,
            "author_label": None,
            "created_at": "2015-05-19T00:00:00Z",
            "updated_at": "2015-05-19T00:00:00Z",
            "type": "discussion",
            "title": "Test Title",
            "raw_body": "Test body",
            "rendered_body": "<p>Test body</p>",
            "pinned": False,
            "closed": False,
            "following": False,
            "abuse_flagged": False,
            "voted": False,
            "vote_count": 0,
            "comment_count": 1,
            "unread_comment_count": 1,
            "comment_list_url": "http://testserver/api/discussion/v1/comments/?thread_id=test_thread",
            "endorsed_comment_list_url": None,
            "non_endorsed_comment_list_url": None,
            "editable_fields": ["abuse_flagged", "following", "raw_body", "read", "title", "topic_id", "type", "voted"],
            "read": False,
            "has_endorsed": False,
            "response_count": 0,
        }
        response = self.client.post(
            self.url,
            json.dumps(request_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data, expected_response_data)
        self.assertEqual(
            httpretty.last_request().parsed_body,
            {
                "course_id": [unicode(self.course.id)],
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
        response_data = json.loads(response.content)
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

    def expected_response_data(self, overrides=None):
        """
        create expected response data from comment update endpoint
        """
        response_data = {
            "id": "test_thread",
            "course_id": unicode(self.course.id),
            "topic_id": "original_topic",
            "group_id": None,
            "group_name": None,
            "author": self.user.username,
            "author_label": None,
            "created_at": "1970-01-01T00:00:00Z",
            "updated_at": "1970-01-01T00:00:00Z",
            "type": "discussion",
            "title": "Original Title",
            "raw_body": "Original body",
            "rendered_body": "<p>Original body</p>",
            "pinned": False,
            "closed": False,
            "following": False,
            "abuse_flagged": False,
            "voted": False,
            "vote_count": 0,
            "comment_count": 0,
            "unread_comment_count": 0,
            "comment_list_url": "http://testserver/api/discussion/v1/comments/?thread_id=test_thread",
            "endorsed_comment_list_url": None,
            "non_endorsed_comment_list_url": None,
            "editable_fields": [],
            "read": False,
            "has_endorsed": False,
            "response_count": 0,
        }
        response_data.update(overrides or {})
        return response_data

    def test_basic(self):
        self.register_get_user_response(self.user)
        self.register_thread({"created_at": "Test Created Date", "updated_at": "Test Updated Date"})
        request_data = {"raw_body": "Edited body"}
        response = self.request_patch(request_data)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(
            response_data,
            self.expected_response_data({
                "raw_body": "Edited body",
                "rendered_body": "<p>Edited body</p>",
                "editable_fields": [
                    "abuse_flagged", "following", "raw_body", "read", "title", "topic_id", "type", "voted"
                ],
                "created_at": "Test Created Date",
                "updated_at": "Test Updated Date",
                "comment_count": 1,
            })
        )
        self.assertEqual(
            httpretty.last_request().parsed_body,
            {
                "course_id": [unicode(self.course.id)],
                "commentable_id": ["original_topic"],
                "thread_type": ["discussion"],
                "title": ["Original Title"],
                "body": ["Edited body"],
                "user_id": [str(self.user.id)],
                "anonymous": ["False"],
                "anonymous_to_peers": ["False"],
                "closed": ["False"],
                "pinned": ["False"],
                "read": ["False"],
                "requested_user_id": [str(self.user.id)],
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
        response_data = json.loads(response.content)
        self.assertEqual(response_data, expected_response_data)

    @ddt.data(
        ("abuse_flagged", True),
        ("abuse_flagged", False),
    )
    @ddt.unpack
    def test_closed_thread(self, field, value):
        self.register_get_user_response(self.user)
        self.register_thread({"closed": True})
        self.register_flag_response("thread", "test_thread")
        request_data = {field: value}
        response = self.request_patch(request_data)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(
            response_data,
            self.expected_response_data({
                "closed": True,
                "abuse_flagged": value,
                "editable_fields": ["abuse_flagged", "read"],
                "comment_count": 1,
                "unread_comment_count": 1,
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
        self.register_thread()
        request_data = {"read": True}
        response = self.request_patch(request_data)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(
            response_data,
            self.expected_response_data({
                "comment_count": 1,
                "read": True,
                "editable_fields": [
                    "abuse_flagged", "following", "raw_body", "read", "title", "topic_id", "type", "voted"
                ],
            })
        )

        self.assertEqual(
            httpretty.last_request().parsed_body,
            {
                "course_id": [unicode(self.course.id)],
                "commentable_id": ["original_topic"],
                "thread_type": ["discussion"],
                "title": ["Original Title"],
                "body": ["Original body"],
                "user_id": [str(self.user.id)],
                "anonymous": ["False"],
                "anonymous_to_peers": ["False"],
                "closed": ["False"],
                "pinned": ["False"],
                "read": ["True"],
                "requested_user_id": [str(self.user.id)],
            }
        )

    def test_patch_read_non_owner_user(self):
        self.register_get_user_response(self.user)
        thread_owner_user = UserFactory.create(password=self.password)
        CourseEnrollmentFactory.create(user=thread_owner_user, course_id=self.course.id)
        self.register_get_user_response(thread_owner_user)
        self.register_thread({"username": thread_owner_user.username, "user_id": str(thread_owner_user.id)})

        request_data = {"read": True}
        response = self.request_patch(request_data)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(
            response_data,
            self.expected_response_data({
                "author": str(thread_owner_user.username),
                "comment_count": 1,
                "read": True,
                "editable_fields": [
                    "abuse_flagged", "following", "read", "voted"
                ],
            })
        )

        self.assertEqual(
            httpretty.last_request().parsed_body,
            {
                "course_id": [unicode(self.course.id)],
                "commentable_id": ["original_topic"],
                "thread_type": ["discussion"],
                "title": ["Original Title"],
                "body": ["Original body"],
                "user_id": [str(thread_owner_user.id)],
                "anonymous": ["False"],
                "anonymous_to_peers": ["False"],
                "closed": ["False"],
                "pinned": ["False"],
                "read": ["True"],
                "requested_user_id": [str(self.user.id)],
            }
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
            "course_id": unicode(self.course.id),
            "username": self.user.username,
            "user_id": str(self.user.id),
        })
        self.register_get_thread_response(cs_thread)
        self.register_delete_thread_response(self.thread_id)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, "")
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
class CommentViewSetListTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for CommentViewSet list"""
    def setUp(self):
        super(CommentViewSetListTest, self).setUp()
        self.author = UserFactory.create()
        self.url = reverse("comment-list")
        self.thread_id = "test_thread"

    def make_minimal_cs_thread(self, overrides=None):
        """
        Create a thread with the given overrides, plus the course_id if not
        already in overrides.
        """
        overrides = overrides.copy() if overrides else {}
        overrides.setdefault("course_id", unicode(self.course.id))
        return make_minimal_cs_thread(overrides)

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
            {"developer_message": "Not found."}
        )

    def test_basic(self):
        self.register_get_user_response(self.user, upvoted_ids=["test_comment"])
        source_comments = [{
            "type": "comment",
            "id": "test_comment",
            "thread_id": self.thread_id,
            "parent_id": None,
            "user_id": str(self.author.id),
            "username": self.author.username,
            "anonymous": False,
            "anonymous_to_peers": False,
            "created_at": "2015-05-11T00:00:00Z",
            "updated_at": "2015-05-11T11:11:11Z",
            "body": "Test body",
            "endorsed": False,
            "abuse_flaggers": [],
            "votes": {"up_count": 4},
        }]
        expected_comments = [{
            "id": "test_comment",
            "thread_id": self.thread_id,
            "parent_id": None,
            "author": self.author.username,
            "author_label": None,
            "created_at": "2015-05-11T00:00:00Z",
            "updated_at": "2015-05-11T11:11:11Z",
            "raw_body": "Test body",
            "rendered_body": "<p>Test body</p>",
            "endorsed": False,
            "endorsed_by": None,
            "endorsed_by_label": None,
            "endorsed_at": None,
            "abuse_flagged": False,
            "voted": True,
            "vote_count": 4,
            "editable_fields": ["abuse_flagged", "voted"],
            "children": [],
        }]
        self.register_get_thread_response({
            "id": self.thread_id,
            "course_id": unicode(self.course.id),
            "thread_type": "discussion",
            "children": source_comments,
            "resp_total": 100,
        })
        response = self.client.get(self.url, {"thread_id": self.thread_id})
        self.assert_response_correct(
            response,
            200,
            {
                "results": expected_comments,
                "next": "http://testserver/api/discussion/v1/comments/?page=2&thread_id={}".format(
                    self.thread_id
                ),
                "previous": None,
            }
        )
        self.assert_query_params_equal(
            httpretty.httpretty.latest_requests[-2],
            {
                "recursive": ["False"],
                "resp_skip": ["0"],
                "resp_limit": ["10"],
                "user_id": [str(self.user.id)],
                "mark_as_read": ["False"],
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
            "course_id": unicode(self.course.id),
            "thread_type": "discussion",
            "children": [],
            "resp_total": 10,
        }))
        response = self.client.get(
            self.url,
            {"thread_id": self.thread_id, "page": "18", "page_size": "4"}
        )
        self.assert_response_correct(
            response,
            404,
            {"developer_message": "Not found."}
        )
        self.assert_query_params_equal(
            httpretty.httpretty.latest_requests[-2],
            {
                "recursive": ["False"],
                "resp_skip": ["68"],
                "resp_limit": ["4"],
                "user_id": [str(self.user.id)],
                "mark_as_read": ["False"],
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
            "endorsed_responses": [make_minimal_cs_comment({"id": "endorsed_comment"})],
            "non_endorsed_responses": [make_minimal_cs_comment({"id": "non_endorsed_comment"})],
            "non_endorsed_resp_total": 1,
        })
        self.register_get_thread_response(thread)
        response = self.client.get(self.url, {
            "thread_id": thread["id"],
            "endorsed": endorsed,
        })
        parsed_content = json.loads(response.content)
        self.assertEqual(parsed_content["results"][0]["id"], comment_id)


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
            "course_id": unicode(self.course.id),
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
        self.assertEqual(response.content, "")
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
        }
        response = self.client.post(
            self.url,
            json.dumps(request_data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data, expected_response_data)
        self.assertEqual(
            urlparse(httpretty.last_request().path).path,
            "/api/v1/threads/test_thread/comments"
        )
        self.assertEqual(
            httpretty.last_request().parsed_body,
            {
                "course_id": [unicode(self.course.id)],
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
        response_data = json.loads(response.content)
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
        }
        response_data.update(overrides or {})
        return response_data

    def test_basic(self):
        self.register_thread()
        self.register_comment({"created_at": "Test Created Date", "updated_at": "Test Updated Date"})
        request_data = {"raw_body": "Edited body"}
        response = self.request_patch(request_data)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
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
                "course_id": [unicode(self.course.id)],
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
        response_data = json.loads(response.content)
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
        response_data = json.loads(response.content)
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
class ThreadViewSetRetrieveTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for ThreadViewSet Retrieve"""
    def setUp(self):
        super(ThreadViewSetRetrieveTest, self).setUp()
        self.url = reverse("thread-detail", kwargs={"thread_id": "test_thread"})
        self.thread_id = "test_thread"

    def test_basic(self):
        self.register_get_user_response(self.user)
        cs_thread = make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": unicode(self.course.id),
            "commentable_id": "test_topic",
            "username": self.user.username,
            "user_id": str(self.user.id),
            "title": "Test Title",
            "body": "Test body",
            "created_at": "2015-05-29T00:00:00Z",
            "updated_at": "2015-05-29T00:00:00Z"
        })
        expected_response_data = {
            "author": self.user.username,
            "author_label": None,
            "created_at": "2015-05-29T00:00:00Z",
            "updated_at": "2015-05-29T00:00:00Z",
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
            "unread_comment_count": 1,
            "comment_list_url": "http://testserver/api/discussion/v1/comments/?thread_id=test_thread",
            "endorsed_comment_list_url": None,
            "non_endorsed_comment_list_url": None,
            "read": False,
            "has_endorsed": False,
            "id": "test_thread",
            "type": "discussion",
            "response_count": 0,
        }
        self.register_get_thread_response(cs_thread)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), expected_response_data)
        self.assertEqual(httpretty.last_request().method, "GET")

    def test_retrieve_nonexistent_thread(self):
        self.register_get_thread_error_response(self.thread_id, 404)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


@httpretty.activate
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CommentViewSetRetrieveTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
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
            "course_id": unicode(self.course.id),
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
            "course_id": unicode(self.course.id),
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
            "editable_fields": ["abuse_flagged", "raw_body", "voted"]
        }

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['results'][0], expected_response_data)

    def test_retrieve_nonexistent_comment(self):
        self.register_get_comment_error_response(self.comment_id, 404)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
