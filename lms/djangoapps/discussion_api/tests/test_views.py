"""
Tests for Discussion API views
"""
from datetime import datetime
import json
from urlparse import urlparse

import httpretty
import mock
from pytz import UTC

from django.core.urlresolvers import reverse

from rest_framework.test import APIClient

from discussion_api.tests.utils import (
    CommentsServiceMockMixin,
    make_minimal_cs_comment,
    make_minimal_cs_thread,
)
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from util.testing import UrlResetMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


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

    def test_not_authenticated(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assert_response_correct(
            response,
            401,
            {"developer_message": "Authentication credentials were not provided."}
        )


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
            {"developer_message": "Not found."}
        )

    def test_get_success(self):
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


class CourseTopicsViewTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for CourseTopicsView"""
    def setUp(self):
        super(CourseTopicsViewTest, self).setUp()
        self.url = reverse("course_topics", kwargs={"course_id": unicode(self.course.id)})

    def test_404(self):
        response = self.client.get(
            reverse("course_topics", kwargs={"course_id": "non/existent/course"})
        )
        self.assert_response_correct(
            response,
            404,
            {"developer_message": "Not found."}
        )

    def test_get_success(self):
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


@httpretty.activate
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
            {"developer_message": "Not found."}
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
            "comment_count": 5,
            "unread_comment_count": 3,
            "comment_list_url": "http://testserver/api/discussion/v1/comments/?thread_id=test_thread",
            "endorsed_comment_list_url": None,
            "non_endorsed_comment_list_url": None,
            "editable_fields": ["abuse_flagged", "following", "voted"],
        }]
        self.register_get_threads_response(source_threads, page=1, num_pages=2)
        response = self.client.get(self.url, {"course_id": unicode(self.course.id)})
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
            "course_id": [unicode(self.course.id)],
            "sort_key": ["date"],
            "sort_order": ["desc"],
            "page": ["1"],
            "per_page": ["10"],
            "recursive": ["False"],
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
            "course_id": [unicode(self.course.id)],
            "sort_key": ["date"],
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
            "course_id": [unicode(self.course.id)],
            "sort_key": ["date"],
            "sort_order": ["desc"],
            "page": ["1"],
            "per_page": ["10"],
            "recursive": ["False"],
            "text": ["test search string"],
        })

    def test_following(self):
        self.register_get_user_response(self.user)
        self.register_subscribed_threads_response(self.user, [], page=1, num_pages=1)
        response = self.client.get(
            self.url,
            {
                "course_id": unicode(self.course.id),
                "page": "1",
                "page_size": "4",
                "following": "True",
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


@httpretty.activate
class ThreadViewSetCreateTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for ThreadViewSet create"""
    def setUp(self):
        super(ThreadViewSetCreateTest, self).setUp()
        self.url = reverse("thread-list")

    def test_basic(self):
        self.register_get_user_response(self.user)
        self.register_post_thread_response({
            "id": "test_thread",
            "username": self.user.username,
            "created_at": "2015-05-19T00:00:00Z",
            "updated_at": "2015-05-19T00:00:00Z",
        })
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
            "comment_count": 0,
            "unread_comment_count": 0,
            "comment_list_url": "http://testserver/api/discussion/v1/comments/?thread_id=test_thread",
            "endorsed_comment_list_url": None,
            "non_endorsed_comment_list_url": None,
            "editable_fields": ["abuse_flagged", "following", "raw_body", "title", "topic_id", "type", "voted"],
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


@httpretty.activate
class ThreadViewSetPartialUpdateTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for ThreadViewSet partial_update"""
    def setUp(self):
        super(ThreadViewSetPartialUpdateTest, self).setUp()
        self.url = reverse("thread-detail", kwargs={"thread_id": "test_thread"})

    def test_basic(self):
        self.register_get_user_response(self.user)
        cs_thread = make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": unicode(self.course.id),
            "commentable_id": "original_topic",
            "username": self.user.username,
            "user_id": str(self.user.id),
            "created_at": "2015-05-29T00:00:00Z",
            "updated_at": "2015-05-29T00:00:00Z",
            "thread_type": "discussion",
            "title": "Original Title",
            "body": "Original body",
        })
        self.register_get_thread_response(cs_thread)
        self.register_put_thread_response(cs_thread)
        request_data = {"raw_body": "Edited body"}
        expected_response_data = {
            "id": "test_thread",
            "course_id": unicode(self.course.id),
            "topic_id": "original_topic",
            "group_id": None,
            "group_name": None,
            "author": self.user.username,
            "author_label": None,
            "created_at": "2015-05-29T00:00:00Z",
            "updated_at": "2015-05-29T00:00:00Z",
            "type": "discussion",
            "title": "Original Title",
            "raw_body": "Edited body",
            "rendered_body": "<p>Edited body</p>",
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
            "editable_fields": ["abuse_flagged", "following", "raw_body", "title", "topic_id", "type", "voted"],
        }
        response = self.client.patch(  # pylint: disable=no-member
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
                "commentable_id": ["original_topic"],
                "thread_type": ["discussion"],
                "title": ["Original Title"],
                "body": ["Edited body"],
                "user_id": [str(self.user.id)],
                "anonymous": ["False"],
                "anonymous_to_peers": ["False"],
                "closed": ["False"],
                "pinned": ["False"],
            }
        )

    def test_error(self):
        self.register_get_user_response(self.user)
        cs_thread = make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": unicode(self.course.id),
            "user_id": str(self.user.id),
        })
        self.register_get_thread_response(cs_thread)
        request_data = {"title": ""}
        response = self.client.patch(  # pylint: disable=no-member
            self.url,
            json.dumps(request_data),
            content_type="application/json"
        )
        expected_response_data = {
            "field_errors": {"title": {"developer_message": "This field is required."}}
        }
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data, expected_response_data)


@httpretty.activate
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


@httpretty.activate
class CommentViewSetListTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for CommentViewSet list"""
    def setUp(self):
        super(CommentViewSetListTest, self).setUp()
        self.author = UserFactory.create()
        self.url = reverse("comment-list")
        self.thread_id = "test_thread"

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
            "children": [],
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
            "children": [],
            "editable_fields": ["abuse_flagged", "voted"],
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
                "next": "http://testserver/api/discussion/v1/comments/?thread_id={}&page=2".format(
                    self.thread_id
                ),
                "previous": None,
            }
        )
        self.assert_query_params_equal(
            httpretty.httpretty.latest_requests[-2],
            {
                "recursive": ["True"],
                "resp_skip": ["0"],
                "resp_limit": ["10"],
                "user_id": [str(self.user.id)],
                "mark_as_read": ["True"],
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
                "recursive": ["True"],
                "resp_skip": ["68"],
                "resp_limit": ["4"],
                "user_id": [str(self.user.id)],
                "mark_as_read": ["True"],
            }
        )


@httpretty.activate
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
class CommentViewSetCreateTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for CommentViewSet create"""
    def setUp(self):
        super(CommentViewSetCreateTest, self).setUp()
        self.url = reverse("comment-list")

    def test_basic(self):
        self.register_get_user_response(self.user)
        self.register_get_thread_response(
            make_minimal_cs_thread({
                "id": "test_thread",
                "course_id": unicode(self.course.id),
                "commentable_id": "test_topic",
            })
        )
        self.register_post_comment_response(
            {
                "id": "test_comment",
                "username": self.user.username,
                "created_at": "2015-05-27T00:00:00Z",
                "updated_at": "2015-05-27T00:00:00Z",
            },
            thread_id="test_thread"
        )
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
            "created_at": "2015-05-27T00:00:00Z",
            "updated_at": "2015-05-27T00:00:00Z",
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


class CommentViewSetPartialUpdateTest(DiscussionAPIViewTestMixin, ModuleStoreTestCase):
    """Tests for CommentViewSet partial_update"""
    def setUp(self):
        super(CommentViewSetPartialUpdateTest, self).setUp()
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.disable)
        self.register_get_user_response(self.user)
        self.url = reverse("comment-detail", kwargs={"comment_id": "test_comment"})
        cs_thread = make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": unicode(self.course.id),
        })
        self.register_get_thread_response(cs_thread)
        cs_comment = make_minimal_cs_comment({
            "id": "test_comment",
            "course_id": cs_thread["course_id"],
            "thread_id": cs_thread["id"],
            "username": self.user.username,
            "user_id": str(self.user.id),
            "created_at": "2015-06-03T00:00:00Z",
            "updated_at": "2015-06-03T00:00:00Z",
            "body": "Original body",
        })
        self.register_get_comment_response(cs_comment)
        self.register_put_comment_response(cs_comment)

    def test_basic(self):
        request_data = {"raw_body": "Edited body"}
        expected_response_data = {
            "id": "test_comment",
            "thread_id": "test_thread",
            "parent_id": None,
            "author": self.user.username,
            "author_label": None,
            "created_at": "2015-06-03T00:00:00Z",
            "updated_at": "2015-06-03T00:00:00Z",
            "raw_body": "Edited body",
            "rendered_body": "<p>Edited body</p>",
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
        response = self.client.patch(  # pylint: disable=no-member
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
                "body": ["Edited body"],
                "course_id": [unicode(self.course.id)],
                "user_id": [str(self.user.id)],
                "anonymous": ["False"],
                "anonymous_to_peers": ["False"],
                "endorsed": ["False"],
            }
        )

    def test_error(self):
        request_data = {"raw_body": ""}
        response = self.client.patch(  # pylint: disable=no-member
            self.url,
            json.dumps(request_data),
            content_type="application/json"
        )
        expected_response_data = {
            "field_errors": {"raw_body": {"developer_message": "This field is required."}}
        }
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data, expected_response_data)
