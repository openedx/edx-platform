"""
Tests for Discussion API views
"""
from datetime import datetime
import json

import httpretty
import mock
from pytz import UTC

from django.core.urlresolvers import reverse

from discussion_api.tests.utils import CommentsServiceMockMixin, make_minimal_cs_thread
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
                    "children": []
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
            {"field_errors": {"course_id": "This field is required."}}
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
            "pinned": False,
            "closed": False,
            "following": False,
            "abuse_flagged": False,
            "voted": True,
            "vote_count": 4,
            "comment_count": 5,
            "unread_comment_count": 3,
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
            {"field_errors": {"thread_id": "This field is required."}}
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
            "abuse_flagged": False,
            "voted": True,
            "vote_count": 4,
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
