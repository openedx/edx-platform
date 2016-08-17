"""
Tests for Discussion API internal interface
"""
from datetime import datetime, timedelta
import itertools
from urlparse import parse_qs, urlparse, urlunparse
from urllib import urlencode

import ddt
import httpretty
import mock
from pytz import UTC

from django.core.exceptions import ValidationError
from django.http import Http404
from django.test.client import RequestFactory

from rest_framework.exceptions import PermissionDenied

from opaque_keys.edx.locator import CourseLocator

from common.test.utils import MockSignalHandlerMixin, disable_signal
from courseware.tests.factories import BetaTesterFactory, StaffFactory
from discussion_api import api
from discussion_api.api import (
    create_comment,
    create_thread,
    delete_comment,
    delete_thread,
    get_comment_list,
    get_course,
    get_course_topics,
    get_thread_list,
    update_comment,
    update_thread,
    get_thread,
)
from discussion_api.tests.utils import (
    CommentsServiceMockMixin,
    make_minimal_cs_comment,
    make_minimal_cs_thread,
)
from django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_MODERATOR,
    FORUM_ROLE_STUDENT,
    Role,
)
from openedx.core.djangoapps.course_groups.models import CourseUserGroupPartitionGroup
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from util.testing import UrlResetMixin
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.partitions.partitions import Group, UserPartition


def _remove_discussion_tab(course, user_id):
    """
    Remove the discussion tab for the course.

    user_id is passed to the modulestore as the editor of the module.
    """
    course.tabs = [tab for tab in course.tabs if not tab.type == 'discussion']
    modulestore().update_item(course, user_id)


def _discussion_disabled_course_for(user):
    """
    Create and return a course with discussions disabled.

    The user passed in will be enrolled in the course.
    """
    course_with_disabled_forums = CourseFactory.create()
    CourseEnrollmentFactory.create(user=user, course_id=course_with_disabled_forums.id)
    _remove_discussion_tab(course_with_disabled_forums, user.id)

    return course_with_disabled_forums


@ddt.ddt
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class GetCourseTest(UrlResetMixin, SharedModuleStoreTestCase):
    """Test for get_course"""

    @classmethod
    def setUpClass(cls):
        super(GetCourseTest, cls).setUpClass()
        cls.course = CourseFactory.create(org="x", course="y", run="z")

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(GetCourseTest, self).setUp()
        self.user = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.request = RequestFactory().get("/dummy")
        self.request.user = self.user

    def test_nonexistent_course(self):
        with self.assertRaises(Http404):
            get_course(self.request, CourseLocator.from_string("non/existent/course"))

    def test_not_enrolled(self):
        unenrolled_user = UserFactory.create()
        self.request.user = unenrolled_user
        with self.assertRaises(Http404):
            get_course(self.request, self.course.id)

    def test_discussions_disabled(self):
        with self.assertRaises(Http404):
            get_course(self.request, _discussion_disabled_course_for(self.user).id)

    def test_basic(self):
        self.assertEqual(
            get_course(self.request, self.course.id),
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

    def test_blackout(self):
        # A variety of formats is accepted
        self.course.discussion_blackouts = [
            ["2015-06-09T00:00:00Z", "6-10-15"],
            [1433980800000, datetime(2015, 6, 12)],
        ]
        modulestore().update_item(self.course, self.user.id)
        result = get_course(self.request, self.course.id)
        self.assertEqual(
            result["blackouts"],
            [
                {"start": "2015-06-09T00:00:00+00:00", "end": "2015-06-10T00:00:00+00:00"},
                {"start": "2015-06-11T00:00:00+00:00", "end": "2015-06-12T00:00:00+00:00"},
            ]
        )

    @ddt.data(None, "not a datetime", "2015", [])
    def test_blackout_errors(self, bad_value):
        self.course.discussion_blackouts = [
            [bad_value, "2015-06-09T00:00:00Z"],
            ["2015-06-10T00:00:00Z", "2015-06-11T00:00:00Z"],
        ]
        modulestore().update_item(self.course, self.user.id)
        result = get_course(self.request, self.course.id)
        self.assertEqual(result["blackouts"], [])


@mock.patch.dict("django.conf.settings.FEATURES", {"DISABLE_START_DATES": False})
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class GetCourseTopicsTest(UrlResetMixin, ModuleStoreTestCase):
    """Test for get_course_topics"""
    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(GetCourseTopicsTest, self).setUp()
        self.maxDiff = None  # pylint: disable=invalid-name
        self.partition = UserPartition(
            0,
            "partition",
            "Test Partition",
            [Group(0, "Cohort A"), Group(1, "Cohort B")],
            scheme_id="cohort"
        )
        self.course = CourseFactory.create(
            org="x",
            course="y",
            run="z",
            start=datetime.now(UTC),
            discussion_topics={"Test Topic": {"id": "non-courseware-topic-id"}},
            user_partitions=[self.partition],
            cohort_config={"cohorted": True},
            days_early_for_beta=3
        )
        self.user = UserFactory.create()
        self.request = RequestFactory().get("/dummy")
        self.request.user = self.user
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

    def make_discussion_module(self, topic_id, category, subcategory, **kwargs):
        """Build a discussion module in self.course"""
        ItemFactory.create(
            parent_location=self.course.location,
            category="discussion",
            discussion_id=topic_id,
            discussion_category=category,
            discussion_target=subcategory,
            **kwargs
        )

    def get_thread_list_url(self, topic_id_list):
        """
        Returns the URL for the thread_list_url field, given a list of topic_ids
        """
        path = "http://testserver/api/discussion/v1/threads/"
        query_list = [("course_id", unicode(self.course.id))] + [("topic_id", topic_id) for topic_id in topic_id_list]
        return urlunparse(("", "", path, "", urlencode(query_list), ""))

    def get_course_topics(self):
        """
        Get course topics for self.course, using the given user or self.user if
        not provided, and generating absolute URIs with a test scheme/host.
        """
        return get_course_topics(self.request, self.course.id)

    def make_expected_tree(self, topic_id, name, children=None):
        """
        Build an expected result tree given a topic id, display name, and
        children
        """
        topic_id_list = [topic_id] if topic_id else [child["id"] for child in children]
        children = children or []
        node = {
            "id": topic_id,
            "name": name,
            "children": children,
            "thread_list_url": self.get_thread_list_url(topic_id_list)
        }

        return node

    def test_nonexistent_course(self):
        with self.assertRaises(Http404):
            get_course_topics(self.request, CourseLocator.from_string("non/existent/course"))

    def test_not_enrolled(self):
        unenrolled_user = UserFactory.create()
        self.request.user = unenrolled_user
        with self.assertRaises(Http404):
            self.get_course_topics()

    def test_discussions_disabled(self):
        _remove_discussion_tab(self.course, self.user.id)
        with self.assertRaises(Http404):
            self.get_course_topics()

    def test_without_courseware(self):
        actual = self.get_course_topics()
        expected = {
            "courseware_topics": [],
            "non_courseware_topics": [
                self.make_expected_tree("non-courseware-topic-id", "Test Topic")
            ],
        }
        self.assertEqual(actual, expected)

    def test_with_courseware(self):
        self.make_discussion_module("courseware-topic-id", "Foo", "Bar")
        actual = self.get_course_topics()
        expected = {
            "courseware_topics": [
                self.make_expected_tree(
                    None,
                    "Foo",
                    [self.make_expected_tree("courseware-topic-id", "Bar")]
                ),
            ],
            "non_courseware_topics": [
                self.make_expected_tree("non-courseware-topic-id", "Test Topic")
            ],
        }
        self.assertEqual(actual, expected)

    def test_many(self):
        with self.store.bulk_operations(self.course.id, emit_signals=False):
            self.course.discussion_topics = {
                "A": {"id": "non-courseware-1"},
                "B": {"id": "non-courseware-2"},
            }
            self.store.update_item(self.course, self.user.id)
            self.make_discussion_module("courseware-1", "A", "1")
            self.make_discussion_module("courseware-2", "A", "2")
            self.make_discussion_module("courseware-3", "B", "1")
            self.make_discussion_module("courseware-4", "B", "2")
            self.make_discussion_module("courseware-5", "C", "1")
        actual = self.get_course_topics()
        expected = {
            "courseware_topics": [
                self.make_expected_tree(
                    None,
                    "A",
                    [
                        self.make_expected_tree("courseware-1", "1"),
                        self.make_expected_tree("courseware-2", "2"),
                    ]
                ),
                self.make_expected_tree(
                    None,
                    "B",
                    [
                        self.make_expected_tree("courseware-3", "1"),
                        self.make_expected_tree("courseware-4", "2"),
                    ]
                ),
                self.make_expected_tree(
                    None,
                    "C",
                    [self.make_expected_tree("courseware-5", "1")]
                ),
            ],
            "non_courseware_topics": [
                self.make_expected_tree("non-courseware-1", "A"),
                self.make_expected_tree("non-courseware-2", "B"),
            ],
        }
        self.assertEqual(actual, expected)

    def test_sort_key(self):
        with self.store.bulk_operations(self.course.id, emit_signals=False):
            self.course.discussion_topics = {
                "W": {"id": "non-courseware-1", "sort_key": "Z"},
                "X": {"id": "non-courseware-2"},
                "Y": {"id": "non-courseware-3", "sort_key": "Y"},
                "Z": {"id": "non-courseware-4", "sort_key": "W"},
            }
            self.store.update_item(self.course, self.user.id)
            self.make_discussion_module("courseware-1", "First", "A", sort_key="D")
            self.make_discussion_module("courseware-2", "First", "B", sort_key="B")
            self.make_discussion_module("courseware-3", "First", "C", sort_key="E")
            self.make_discussion_module("courseware-4", "Second", "A", sort_key="F")
            self.make_discussion_module("courseware-5", "Second", "B", sort_key="G")
            self.make_discussion_module("courseware-6", "Second", "C")
            self.make_discussion_module("courseware-7", "Second", "D", sort_key="A")

        actual = self.get_course_topics()
        expected = {
            "courseware_topics": [
                self.make_expected_tree(
                    None,
                    "First",
                    [
                        self.make_expected_tree("courseware-2", "B"),
                        self.make_expected_tree("courseware-1", "A"),
                        self.make_expected_tree("courseware-3", "C"),
                    ]
                ),
                self.make_expected_tree(
                    None,
                    "Second",
                    [
                        self.make_expected_tree("courseware-7", "D"),
                        self.make_expected_tree("courseware-6", "C"),
                        self.make_expected_tree("courseware-4", "A"),
                        self.make_expected_tree("courseware-5", "B"),
                    ]
                ),
            ],
            "non_courseware_topics": [
                self.make_expected_tree("non-courseware-4", "Z"),
                self.make_expected_tree("non-courseware-2", "X"),
                self.make_expected_tree("non-courseware-3", "Y"),
                self.make_expected_tree("non-courseware-1", "W"),
            ],
        }
        self.assertEqual(actual, expected)

    def test_access_control(self):
        """
        Test that only topics that a user has access to are returned. The
        ways in which a user may not have access are:

        * Module is visible to staff only
        * Module has a start date in the future
        * Module is accessible only to a group the user is not in

        Also, there is a case that ensures that a category with no accessible
        subcategories does not appear in the result.
        """
        beta_tester = BetaTesterFactory.create(course_key=self.course.id)
        CourseEnrollmentFactory.create(user=beta_tester, course_id=self.course.id)
        staff = StaffFactory.create(course_key=self.course.id)
        for user, group_idx in [(self.user, 0), (beta_tester, 1)]:
            cohort = CohortFactory.create(
                course_id=self.course.id,
                name=self.partition.groups[group_idx].name,
                users=[user]
            )
            CourseUserGroupPartitionGroup.objects.create(
                course_user_group=cohort,
                partition_id=self.partition.id,
                group_id=self.partition.groups[group_idx].id
            )

        with self.store.bulk_operations(self.course.id, emit_signals=False):
            self.make_discussion_module("courseware-1", "First", "Everybody")
            self.make_discussion_module(
                "courseware-2",
                "First",
                "Cohort A",
                group_access={self.partition.id: [self.partition.groups[0].id]}
            )
            self.make_discussion_module(
                "courseware-3",
                "First",
                "Cohort B",
                group_access={self.partition.id: [self.partition.groups[1].id]}
            )
            self.make_discussion_module("courseware-4", "Second", "Staff Only", visible_to_staff_only=True)
            self.make_discussion_module(
                "courseware-5",
                "Second",
                "Future Start Date",
                start=datetime.now(UTC) + timedelta(days=1)
            )

        student_actual = self.get_course_topics()
        student_expected = {
            "courseware_topics": [
                self.make_expected_tree(
                    None,
                    "First",
                    [
                        self.make_expected_tree("courseware-2", "Cohort A"),
                        self.make_expected_tree("courseware-1", "Everybody"),
                    ]
                ),
            ],
            "non_courseware_topics": [
                self.make_expected_tree("non-courseware-topic-id", "Test Topic"),
            ],
        }
        self.assertEqual(student_actual, student_expected)
        self.request.user = beta_tester
        beta_actual = self.get_course_topics()
        beta_expected = {
            "courseware_topics": [
                self.make_expected_tree(
                    None,
                    "First",
                    [
                        self.make_expected_tree("courseware-3", "Cohort B"),
                        self.make_expected_tree("courseware-1", "Everybody"),
                    ]
                ),
                self.make_expected_tree(
                    None,
                    "Second",
                    [self.make_expected_tree("courseware-5", "Future Start Date")]
                ),
            ],
            "non_courseware_topics": [
                self.make_expected_tree("non-courseware-topic-id", "Test Topic"),
            ],
        }
        self.assertEqual(beta_actual, beta_expected)

        self.request.user = staff
        staff_actual = self.get_course_topics()
        staff_expected = {
            "courseware_topics": [
                self.make_expected_tree(
                    None,
                    "First",
                    [
                        self.make_expected_tree("courseware-2", "Cohort A"),
                        self.make_expected_tree("courseware-3", "Cohort B"),
                        self.make_expected_tree("courseware-1", "Everybody"),
                    ]
                ),
                self.make_expected_tree(
                    None,
                    "Second",
                    [
                        self.make_expected_tree("courseware-5", "Future Start Date"),
                        self.make_expected_tree("courseware-4", "Staff Only"),
                    ]
                ),
            ],
            "non_courseware_topics": [
                self.make_expected_tree("non-courseware-topic-id", "Test Topic"),
            ],
        }
        self.assertEqual(staff_actual, staff_expected)


@ddt.ddt
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class GetThreadListTest(CommentsServiceMockMixin, UrlResetMixin, SharedModuleStoreTestCase):
    """Test for get_thread_list"""

    @classmethod
    def setUpClass(cls):
        super(GetThreadListTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(GetThreadListTest, self).setUp()
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.disable)
        self.maxDiff = None  # pylint: disable=invalid-name
        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/test_path")
        self.request.user = self.user
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.author = UserFactory.create()
        self.cohort = CohortFactory.create(course_id=self.course.id)

    def get_thread_list(
            self,
            threads,
            page=1,
            page_size=1,
            num_pages=1,
            course=None,
            topic_id_list=None,
    ):
        """
        Register the appropriate comments service response, then call
        get_thread_list and return the result.
        """
        course = course or self.course
        self.register_get_threads_response(threads, page, num_pages)
        ret = get_thread_list(self.request, course.id, page, page_size, topic_id_list)
        return ret

    def test_nonexistent_course(self):
        with self.assertRaises(Http404):
            get_thread_list(self.request, CourseLocator.from_string("non/existent/course"), 1, 1)

    def test_not_enrolled(self):
        self.request.user = UserFactory.create()
        with self.assertRaises(Http404):
            self.get_thread_list([])

    def test_discussions_disabled(self):
        with self.assertRaises(Http404):
            self.get_thread_list([], course=_discussion_disabled_course_for(self.user))

    def test_empty(self):
        self.assertEqual(
            self.get_thread_list([]),
            {
                "results": [],
                "next": None,
                "previous": None,
                "text_search_rewrite": None,
            }
        )

    def test_get_threads_by_topic_id(self):
        self.get_thread_list([], topic_id_list=["topic_x", "topic_meow"])
        self.assertEqual(urlparse(httpretty.last_request().path).path, "/api/v1/threads")
        self.assert_last_query_params({
            "user_id": [unicode(self.user.id)],
            "course_id": [unicode(self.course.id)],
            "sort_key": ["activity"],
            "sort_order": ["desc"],
            "page": ["1"],
            "per_page": ["1"],
            "recursive": ["False"],
            "commentable_ids": ["topic_x,topic_meow"]
        })

    def test_basic_query_params(self):
        self.get_thread_list([], page=6, page_size=14)
        self.assert_last_query_params({
            "user_id": [unicode(self.user.id)],
            "course_id": [unicode(self.course.id)],
            "sort_key": ["activity"],
            "sort_order": ["desc"],
            "page": ["6"],
            "per_page": ["14"],
            "recursive": ["False"],
        })

    def test_thread_content(self):
        source_threads = [
            {
                "type": "thread",
                "id": "test_thread_id_0",
                "course_id": unicode(self.course.id),
                "commentable_id": "topic_x",
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
                "endorsed": True,
                "read": True,
            },
            {
                "type": "thread",
                "id": "test_thread_id_1",
                "course_id": unicode(self.course.id),
                "commentable_id": "topic_y",
                "group_id": self.cohort.id,
                "user_id": str(self.author.id),
                "username": self.author.username,
                "anonymous": False,
                "anonymous_to_peers": False,
                "created_at": "2015-04-28T22:22:22Z",
                "updated_at": "2015-04-28T00:33:33Z",
                "thread_type": "question",
                "title": "Another Test Title",
                "body": "More content",
                "pinned": False,
                "closed": False,
                "abuse_flaggers": [],
                "votes": {"up_count": 9},
                "comments_count": 18,
                "unread_comments_count": 0,
                "endorsed": False,
                "read": False,
            },
        ]
        expected_threads = [
            {
                "id": "test_thread_id_0",
                "course_id": unicode(self.course.id),
                "topic_id": "topic_x",
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
                "voted": False,
                "vote_count": 4,
                "comment_count": 6,
                "unread_comment_count": 3,
                "comment_list_url": "http://testserver/api/discussion/v1/comments/?thread_id=test_thread_id_0",
                "endorsed_comment_list_url": None,
                "non_endorsed_comment_list_url": None,
                "editable_fields": ["abuse_flagged", "following", "read", "voted"],
                "has_endorsed": True,
                "read": True,
            },
            {
                "id": "test_thread_id_1",
                "course_id": unicode(self.course.id),
                "topic_id": "topic_y",
                "group_id": self.cohort.id,
                "group_name": self.cohort.name,
                "author": self.author.username,
                "author_label": None,
                "created_at": "2015-04-28T22:22:22Z",
                "updated_at": "2015-04-28T00:33:33Z",
                "type": "question",
                "title": "Another Test Title",
                "raw_body": "More content",
                "rendered_body": "<p>More content</p>",
                "pinned": False,
                "closed": False,
                "following": False,
                "abuse_flagged": False,
                "voted": False,
                "vote_count": 9,
                "comment_count": 19,
                "unread_comment_count": 1,
                "comment_list_url": None,
                "endorsed_comment_list_url": (
                    "http://testserver/api/discussion/v1/comments/?thread_id=test_thread_id_1&endorsed=True"
                ),
                "non_endorsed_comment_list_url": (
                    "http://testserver/api/discussion/v1/comments/?thread_id=test_thread_id_1&endorsed=False"
                ),
                "editable_fields": ["abuse_flagged", "following", "read", "voted"],
                "has_endorsed": False,
                "read": False,
            },
        ]
        self.assertEqual(
            self.get_thread_list(source_threads),
            {
                "results": expected_threads,
                "next": None,
                "previous": None,
                "text_search_rewrite": None,
            }
        )

    @ddt.data(
        *itertools.product(
            [
                FORUM_ROLE_ADMINISTRATOR,
                FORUM_ROLE_MODERATOR,
                FORUM_ROLE_COMMUNITY_TA,
                FORUM_ROLE_STUDENT,
            ],
            [True, False]
        )
    )
    @ddt.unpack
    def test_request_group(self, role_name, course_is_cohorted):
        cohort_course = CourseFactory.create(cohort_config={"cohorted": course_is_cohorted})
        CourseEnrollmentFactory.create(user=self.user, course_id=cohort_course.id)
        CohortFactory.create(course_id=cohort_course.id, users=[self.user])
        role = Role.objects.create(name=role_name, course_id=cohort_course.id)
        role.users = [self.user]
        self.get_thread_list([], course=cohort_course)
        actual_has_group = "group_id" in httpretty.last_request().querystring
        expected_has_group = (course_is_cohorted and role_name == FORUM_ROLE_STUDENT)
        self.assertEqual(actual_has_group, expected_has_group)

    def test_pagination(self):
        # N.B. Empty thread list is not realistic but convenient for this test
        self.assertEqual(
            self.get_thread_list([], page=1, num_pages=3),
            {
                "results": [],
                "next": "http://testserver/test_path?page=2",
                "previous": None,
                "text_search_rewrite": None,
            }
        )
        self.assertEqual(
            self.get_thread_list([], page=2, num_pages=3),
            {
                "results": [],
                "next": "http://testserver/test_path?page=3",
                "previous": "http://testserver/test_path?page=1",
                "text_search_rewrite": None,
            }
        )
        self.assertEqual(
            self.get_thread_list([], page=3, num_pages=3),
            {
                "results": [],
                "next": None,
                "previous": "http://testserver/test_path?page=2",
                "text_search_rewrite": None,
            }
        )

        # Test page past the last one
        self.register_get_threads_response([], page=3, num_pages=3)
        with self.assertRaises(Http404):
            get_thread_list(self.request, self.course.id, page=4, page_size=10)

    @ddt.data(None, "rewritten search string")
    def test_text_search(self, text_search_rewrite):
        self.register_get_threads_search_response([], text_search_rewrite)
        self.assertEqual(
            get_thread_list(
                self.request,
                self.course.id,
                page=1,
                page_size=10,
                text_search="test search string"
            ),
            {
                "results": [],
                "next": None,
                "previous": None,
                "text_search_rewrite": text_search_rewrite,
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
            "text": ["test search string"],
        })

    def test_following(self):
        self.register_subscribed_threads_response(self.user, [], page=1, num_pages=1)
        result = get_thread_list(
            self.request,
            self.course.id,
            page=1,
            page_size=11,
            following=True,
        )
        self.assertEqual(
            result,
            {"results": [], "next": None, "previous": None, "text_search_rewrite": None}
        )
        self.assertEqual(
            urlparse(httpretty.last_request().path).path,
            "/api/v1/users/{}/subscribed_threads".format(self.user.id)
        )
        self.assert_last_query_params({
            "user_id": [unicode(self.user.id)],
            "course_id": [unicode(self.course.id)],
            "sort_key": ["activity"],
            "sort_order": ["desc"],
            "page": ["1"],
            "per_page": ["11"],
        })

    @ddt.data("unanswered", "unread")
    def test_view_query(self, query):
        self.register_get_threads_response([], page=1, num_pages=1)
        result = get_thread_list(
            self.request,
            self.course.id,
            page=1,
            page_size=11,
            view=query,
        )
        self.assertEqual(
            result,
            {"results": [], "next": None, "previous": None, "text_search_rewrite": None}
        )
        self.assertEqual(
            urlparse(httpretty.last_request().path).path,
            "/api/v1/threads"
        )
        self.assert_last_query_params({
            "user_id": [unicode(self.user.id)],
            "course_id": [unicode(self.course.id)],
            "sort_key": ["activity"],
            "sort_order": ["desc"],
            "page": ["1"],
            "per_page": ["11"],
            "recursive": ["False"],
            query: ["true"],
        })

    @ddt.data(
        ("last_activity_at", "activity"),
        ("comment_count", "comments"),
        ("vote_count", "votes")
    )
    @ddt.unpack
    def test_order_by_query(self, http_query, cc_query):
        """
        Tests the order_by parameter

        Arguments:
            http_query (str): Query string sent in the http request
            cc_query (str): Query string used for the comments client service
        """
        self.register_get_threads_response([], page=1, num_pages=1)
        result = get_thread_list(
            self.request,
            self.course.id,
            page=1,
            page_size=11,
            order_by=http_query,
        )
        self.assertEqual(
            result,
            {"results": [], "next": None, "previous": None, "text_search_rewrite": None}
        )
        self.assertEqual(
            urlparse(httpretty.last_request().path).path,
            "/api/v1/threads"
        )
        self.assert_last_query_params({
            "user_id": [unicode(self.user.id)],
            "course_id": [unicode(self.course.id)],
            "sort_key": [cc_query],
            "sort_order": ["desc"],
            "page": ["1"],
            "per_page": ["11"],
            "recursive": ["False"],
        })

    @ddt.data("asc", "desc")
    def test_order_direction_query(self, http_query):
        self.register_get_threads_response([], page=1, num_pages=1)
        result = get_thread_list(
            self.request,
            self.course.id,
            page=1,
            page_size=11,
            order_direction=http_query,
        )
        self.assertEqual(
            result,
            {"results": [], "next": None, "previous": None, "text_search_rewrite": None}
        )
        self.assertEqual(
            urlparse(httpretty.last_request().path).path,
            "/api/v1/threads"
        )
        self.assert_last_query_params({
            "user_id": [unicode(self.user.id)],
            "course_id": [unicode(self.course.id)],
            "sort_key": ["activity"],
            "sort_order": [http_query],
            "page": ["1"],
            "per_page": ["11"],
            "recursive": ["False"],
        })


@ddt.ddt
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class GetCommentListTest(CommentsServiceMockMixin, SharedModuleStoreTestCase):
    """Test for get_comment_list"""

    @classmethod
    def setUpClass(cls):
        super(GetCommentListTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(GetCommentListTest, self).setUp()
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.disable)
        self.maxDiff = None  # pylint: disable=invalid-name
        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/test_path")
        self.request.user = self.user
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.author = UserFactory.create()

    def make_minimal_cs_thread(self, overrides=None):
        """
        Create a thread with the given overrides, plus the course_id if not
        already in overrides.
        """
        overrides = overrides.copy() if overrides else {}
        overrides.setdefault("course_id", unicode(self.course.id))
        return make_minimal_cs_thread(overrides)

    def get_comment_list(self, thread, endorsed=None, page=1, page_size=1):
        """
        Register the appropriate comments service response, then call
        get_comment_list and return the result.
        """
        self.register_get_thread_response(thread)
        return get_comment_list(self.request, thread["id"], endorsed, page, page_size)

    def test_nonexistent_thread(self):
        thread_id = "nonexistent_thread"
        self.register_get_thread_error_response(thread_id, 404)
        with self.assertRaises(Http404):
            get_comment_list(self.request, thread_id, endorsed=False, page=1, page_size=1)

    def test_nonexistent_course(self):
        with self.assertRaises(Http404):
            self.get_comment_list(self.make_minimal_cs_thread({"course_id": "non/existent/course"}))

    def test_not_enrolled(self):
        self.request.user = UserFactory.create()
        with self.assertRaises(Http404):
            self.get_comment_list(self.make_minimal_cs_thread())

    def test_discussions_disabled(self):
        disabled_course = _discussion_disabled_course_for(self.user)
        with self.assertRaises(Http404):
            self.get_comment_list(
                self.make_minimal_cs_thread(
                    overrides={"course_id": unicode(disabled_course.id)}
                )
            )

    @ddt.data(
        *itertools.product(
            [
                FORUM_ROLE_ADMINISTRATOR,
                FORUM_ROLE_MODERATOR,
                FORUM_ROLE_COMMUNITY_TA,
                FORUM_ROLE_STUDENT,
            ],
            [True, False],
            [True, False],
            ["no_group", "match_group", "different_group"],
        )
    )
    @ddt.unpack
    def test_group_access(
            self,
            role_name,
            course_is_cohorted,
            topic_is_cohorted,
            thread_group_state
    ):
        cohort_course = CourseFactory.create(
            discussion_topics={"Test Topic": {"id": "test_topic"}},
            cohort_config={
                "cohorted": course_is_cohorted,
                "cohorted_discussions": ["test_topic"] if topic_is_cohorted else [],
            }
        )
        CourseEnrollmentFactory.create(user=self.user, course_id=cohort_course.id)
        cohort = CohortFactory.create(course_id=cohort_course.id, users=[self.user])
        role = Role.objects.create(name=role_name, course_id=cohort_course.id)
        role.users = [self.user]
        thread = self.make_minimal_cs_thread({
            "course_id": unicode(cohort_course.id),
            "commentable_id": "test_topic",
            "group_id": (
                None if thread_group_state == "no_group" else
                cohort.id if thread_group_state == "match_group" else
                cohort.id + 1
            ),
        })
        expected_error = (
            role_name == FORUM_ROLE_STUDENT and
            course_is_cohorted and
            topic_is_cohorted and
            thread_group_state == "different_group"
        )
        try:
            self.get_comment_list(thread)
            self.assertFalse(expected_error)
        except Http404:
            self.assertTrue(expected_error)

    @ddt.data(True, False)
    def test_discussion_endorsed(self, endorsed_value):
        with self.assertRaises(ValidationError) as assertion:
            self.get_comment_list(
                self.make_minimal_cs_thread({"thread_type": "discussion"}),
                endorsed=endorsed_value
            )
        self.assertEqual(
            assertion.exception.message_dict,
            {"endorsed": ["This field may not be specified for discussion threads."]}
        )

    def test_question_without_endorsed(self):
        with self.assertRaises(ValidationError) as assertion:
            self.get_comment_list(
                self.make_minimal_cs_thread({"thread_type": "question"}),
                endorsed=None
            )
        self.assertEqual(
            assertion.exception.message_dict,
            {"endorsed": ["This field is required for question threads."]}
        )

    def test_empty(self):
        discussion_thread = self.make_minimal_cs_thread(
            {"thread_type": "discussion", "children": [], "resp_total": 0}
        )
        self.assertEqual(
            self.get_comment_list(discussion_thread),
            {"results": [], "next": None, "previous": None}
        )

        question_thread = self.make_minimal_cs_thread({
            "thread_type": "question",
            "endorsed_responses": [],
            "non_endorsed_responses": [],
            "non_endorsed_resp_total": 0
        })
        self.assertEqual(
            self.get_comment_list(question_thread, endorsed=False),
            {"results": [], "next": None, "previous": None}
        )
        self.assertEqual(
            self.get_comment_list(question_thread, endorsed=True),
            {"results": [], "next": None, "previous": None}
        )

    def test_basic_query_params(self):
        self.get_comment_list(
            self.make_minimal_cs_thread({
                "children": [make_minimal_cs_comment()],
                "resp_total": 71
            }),
            page=6,
            page_size=14
        )
        self.assert_query_params_equal(
            httpretty.httpretty.latest_requests[-2],
            {
                "recursive": ["False"],
                "user_id": [str(self.user.id)],
                "mark_as_read": ["False"],
                "resp_skip": ["70"],
                "resp_limit": ["14"],
            }
        )

    def test_discussion_content(self):
        source_comments = [
            {
                "type": "comment",
                "id": "test_comment_1",
                "thread_id": "test_thread",
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
            },
            {
                "type": "comment",
                "id": "test_comment_2",
                "thread_id": "test_thread",
                "user_id": str(self.author.id),
                "username": self.author.username,
                "anonymous": True,
                "anonymous_to_peers": False,
                "created_at": "2015-05-11T22:22:22Z",
                "updated_at": "2015-05-11T33:33:33Z",
                "body": "More content",
                "endorsed": False,
                "abuse_flaggers": [str(self.user.id)],
                "votes": {"up_count": 7},
                "children": [],
            }
        ]
        expected_comments = [
            {
                "id": "test_comment_1",
                "thread_id": "test_thread",
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
                "voted": False,
                "vote_count": 4,
                "editable_fields": ["abuse_flagged", "voted"],
                "children": [],
            },
            {
                "id": "test_comment_2",
                "thread_id": "test_thread",
                "parent_id": None,
                "author": None,
                "author_label": None,
                "created_at": "2015-05-11T22:22:22Z",
                "updated_at": "2015-05-11T33:33:33Z",
                "raw_body": "More content",
                "rendered_body": "<p>More content</p>",
                "endorsed": False,
                "endorsed_by": None,
                "endorsed_by_label": None,
                "endorsed_at": None,
                "abuse_flagged": True,
                "voted": False,
                "vote_count": 7,
                "editable_fields": ["abuse_flagged", "voted"],
                "children": [],
            },
        ]
        actual_comments = self.get_comment_list(
            self.make_minimal_cs_thread({"children": source_comments})
        )["results"]
        self.assertEqual(actual_comments, expected_comments)

    def test_question_content(self):
        thread = self.make_minimal_cs_thread({
            "thread_type": "question",
            "endorsed_responses": [make_minimal_cs_comment({"id": "endorsed_comment"})],
            "non_endorsed_responses": [make_minimal_cs_comment({"id": "non_endorsed_comment"})],
            "non_endorsed_resp_total": 1,
        })

        endorsed_actual = self.get_comment_list(thread, endorsed=True)
        self.assertEqual(endorsed_actual["results"][0]["id"], "endorsed_comment")

        non_endorsed_actual = self.get_comment_list(thread, endorsed=False)
        self.assertEqual(non_endorsed_actual["results"][0]["id"], "non_endorsed_comment")

    def test_endorsed_by_anonymity(self):
        """
        Ensure thread anonymity is properly considered in serializing
        endorsed_by.
        """
        thread = self.make_minimal_cs_thread({
            "anonymous": True,
            "children": [
                make_minimal_cs_comment({
                    "endorsement": {"user_id": str(self.author.id), "time": "2015-05-18T12:34:56Z"}
                })
            ]
        })
        actual_comments = self.get_comment_list(thread)["results"]
        self.assertIsNone(actual_comments[0]["endorsed_by"])

    @ddt.data(
        ("discussion", None, "children", "resp_total"),
        ("question", False, "non_endorsed_responses", "non_endorsed_resp_total"),
    )
    @ddt.unpack
    def test_cs_pagination(self, thread_type, endorsed_arg, response_field, response_total_field):
        """
        Test cases in which pagination is done by the comments service.

        thread_type is the type of thread (question or discussion).
        endorsed_arg is the value of the endorsed argument.
        repsonse_field is the field in which responses are returned for the
          given thread type.
        response_total_field is the field in which the total number of responses
          is returned for the given thread type.
        """
        # N.B. The mismatch between the number of children and the listed total
        # number of responses is unrealistic but convenient for this test
        thread = self.make_minimal_cs_thread({
            "thread_type": thread_type,
            response_field: [make_minimal_cs_comment()],
            response_total_field: 5,
        })

        # Only page
        actual = self.get_comment_list(thread, endorsed=endorsed_arg, page=1, page_size=5)
        self.assertIsNone(actual["next"])
        self.assertIsNone(actual["previous"])

        # First page of many
        actual = self.get_comment_list(thread, endorsed=endorsed_arg, page=1, page_size=2)
        self.assertEqual(actual["next"], "http://testserver/test_path?page=2")
        self.assertIsNone(actual["previous"])

        # Middle page of many
        actual = self.get_comment_list(thread, endorsed=endorsed_arg, page=2, page_size=2)
        self.assertEqual(actual["next"], "http://testserver/test_path?page=3")
        self.assertEqual(actual["previous"], "http://testserver/test_path?page=1")

        # Last page of many
        actual = self.get_comment_list(thread, endorsed=endorsed_arg, page=3, page_size=2)
        self.assertIsNone(actual["next"])
        self.assertEqual(actual["previous"], "http://testserver/test_path?page=2")

        # Page past the end
        thread = self.make_minimal_cs_thread({
            "thread_type": thread_type,
            response_field: [],
            response_total_field: 5
        })
        with self.assertRaises(Http404):
            self.get_comment_list(thread, endorsed=endorsed_arg, page=2, page_size=5)

    def test_question_endorsed_pagination(self):
        thread = self.make_minimal_cs_thread({
            "thread_type": "question",
            "endorsed_responses": [
                make_minimal_cs_comment({"id": "comment_{}".format(i)}) for i in range(10)
            ]
        })

        def assert_page_correct(page, page_size, expected_start, expected_stop, expected_next, expected_prev):
            """
            Check that requesting the given page/page_size returns the expected
            output
            """
            actual = self.get_comment_list(thread, endorsed=True, page=page, page_size=page_size)
            result_ids = [result["id"] for result in actual["results"]]
            self.assertEqual(
                result_ids,
                ["comment_{}".format(i) for i in range(expected_start, expected_stop)]
            )
            self.assertEqual(
                actual["next"],
                "http://testserver/test_path?page={}".format(expected_next) if expected_next else None
            )
            self.assertEqual(
                actual["previous"],
                "http://testserver/test_path?page={}".format(expected_prev) if expected_prev else None
            )

        # Only page
        assert_page_correct(
            page=1,
            page_size=10,
            expected_start=0,
            expected_stop=10,
            expected_next=None,
            expected_prev=None
        )

        # First page of many
        assert_page_correct(
            page=1,
            page_size=4,
            expected_start=0,
            expected_stop=4,
            expected_next=2,
            expected_prev=None
        )

        # Middle page of many
        assert_page_correct(
            page=2,
            page_size=4,
            expected_start=4,
            expected_stop=8,
            expected_next=3,
            expected_prev=1
        )

        # Last page of many
        assert_page_correct(
            page=3,
            page_size=4,
            expected_start=8,
            expected_stop=10,
            expected_next=None,
            expected_prev=2
        )

        # Page past the end
        with self.assertRaises(Http404):
            self.get_comment_list(thread, endorsed=True, page=2, page_size=10)


@ddt.ddt
@disable_signal(api, 'thread_created')
@disable_signal(api, 'thread_voted')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CreateThreadTest(
        CommentsServiceMockMixin,
        UrlResetMixin,
        SharedModuleStoreTestCase,
        MockSignalHandlerMixin
):
    """Tests for create_thread"""
    @classmethod
    def setUpClass(cls):
        super(CreateThreadTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(CreateThreadTest, self).setUp()
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.disable)
        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/test_path")
        self.request.user = self.user
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.minimal_data = {
            "course_id": unicode(self.course.id),
            "topic_id": "test_topic",
            "type": "discussion",
            "title": "Test Title",
            "raw_body": "Test body",
        }

    @mock.patch("eventtracking.tracker.emit")
    def test_basic(self, mock_emit):
        cs_thread = make_minimal_cs_thread({
            "id": "test_id",
            "username": self.user.username,
            "created_at": "2015-05-19T00:00:00Z",
            "updated_at": "2015-05-19T00:00:00Z",
        })
        self.register_post_thread_response(cs_thread)
        with self.assert_signal_sent(api, 'thread_created', sender=None, user=self.user, exclude_args=('post',)):
            actual = create_thread(self.request, self.minimal_data)
        expected = {
            "id": "test_id",
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
            "comment_list_url": "http://testserver/api/discussion/v1/comments/?thread_id=test_id",
            "endorsed_comment_list_url": None,
            "non_endorsed_comment_list_url": None,
            "editable_fields": ["abuse_flagged", "following", "raw_body", "read", "title", "topic_id", "type", "voted"],
            'read': False,
            'has_endorsed': False,
            'response_count': 0,
        }
        self.assertEqual(actual, expected)
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
        event_name, event_data = mock_emit.call_args[0]
        self.assertEqual(event_name, "edx.forum.thread.created")
        self.assertEqual(
            event_data,
            {
                "commentable_id": "test_topic",
                "group_id": None,
                "thread_type": "discussion",
                "title": "Test Title",
                "anonymous": False,
                "anonymous_to_peers": False,
                "options": {"followed": False},
                "id": "test_id",
                "truncated": False,
                "body": "Test body",
                "url": "",
                "user_forums_roles": [FORUM_ROLE_STUDENT],
                "user_course_roles": [],
            }
        )

    @ddt.data(
        *itertools.product(
            [
                FORUM_ROLE_ADMINISTRATOR,
                FORUM_ROLE_MODERATOR,
                FORUM_ROLE_COMMUNITY_TA,
                FORUM_ROLE_STUDENT,
            ],
            [True, False],
            [True, False],
            ["no_group_set", "group_is_none", "group_is_set"],
        )
    )
    @ddt.unpack
    def test_group_id(self, role_name, course_is_cohorted, topic_is_cohorted, data_group_state):
        """
        Tests whether the user has permission to create a thread with certain
        group_id values.

        If there is no group, user cannot create a thread.
        Else if group is None or set, and the course is not cohorted and/or the
        role is a student, user can create a thread.
        """

        cohort_course = CourseFactory.create(
            discussion_topics={"Test Topic": {"id": "test_topic"}},
            cohort_config={
                "cohorted": course_is_cohorted,
                "cohorted_discussions": ["test_topic"] if topic_is_cohorted else [],
            }
        )
        CourseEnrollmentFactory.create(user=self.user, course_id=cohort_course.id)
        if course_is_cohorted:
            cohort = CohortFactory.create(course_id=cohort_course.id, users=[self.user])
        role = Role.objects.create(name=role_name, course_id=cohort_course.id)
        role.users = [self.user]
        self.register_post_thread_response({})
        data = self.minimal_data.copy()
        data["course_id"] = unicode(cohort_course.id)
        if data_group_state == "group_is_none":
            data["group_id"] = None
        elif data_group_state == "group_is_set":
            if course_is_cohorted:
                data["group_id"] = cohort.id + 1
            else:
                data["group_id"] = 1  # Set to any value since there is no cohort
        expected_error = (
            data_group_state in ["group_is_none", "group_is_set"] and
            (not course_is_cohorted or role_name == FORUM_ROLE_STUDENT)
        )
        try:
            create_thread(self.request, data)
            self.assertFalse(expected_error)
            actual_post_data = httpretty.last_request().parsed_body
            if data_group_state == "group_is_set":
                self.assertEqual(actual_post_data["group_id"], [str(data["group_id"])])
            elif data_group_state == "no_group_set" and course_is_cohorted and topic_is_cohorted:
                self.assertEqual(actual_post_data["group_id"], [str(cohort.id)])
            else:
                self.assertNotIn("group_id", actual_post_data)
        except ValidationError as ex:
            if not expected_error:
                self.fail("Unexpected validation error: {}".format(ex))

    def test_following(self):
        self.register_post_thread_response({"id": "test_id"})
        self.register_subscription_response(self.user)
        data = self.minimal_data.copy()
        data["following"] = "True"
        result = create_thread(self.request, data)
        self.assertEqual(result["following"], True)
        cs_request = httpretty.last_request()
        self.assertEqual(
            urlparse(cs_request.path).path,
            "/api/v1/users/{}/subscriptions".format(self.user.id)
        )
        self.assertEqual(cs_request.method, "POST")
        self.assertEqual(
            cs_request.parsed_body,
            {"source_type": ["thread"], "source_id": ["test_id"]}
        )

    def test_voted(self):
        self.register_post_thread_response({"id": "test_id"})
        self.register_thread_votes_response("test_id")
        data = self.minimal_data.copy()
        data["voted"] = "True"
        with self.assert_signal_sent(api, 'thread_voted', sender=None, user=self.user, exclude_args=('post',)):
            result = create_thread(self.request, data)
        self.assertEqual(result["voted"], True)
        cs_request = httpretty.last_request()
        self.assertEqual(urlparse(cs_request.path).path, "/api/v1/threads/test_id/votes")
        self.assertEqual(cs_request.method, "PUT")
        self.assertEqual(
            cs_request.parsed_body,
            {"user_id": [str(self.user.id)], "value": ["up"]}
        )

    def test_abuse_flagged(self):
        self.register_post_thread_response({"id": "test_id"})
        self.register_thread_flag_response("test_id")
        data = self.minimal_data.copy()
        data["abuse_flagged"] = "True"
        result = create_thread(self.request, data)
        self.assertEqual(result["abuse_flagged"], True)
        cs_request = httpretty.last_request()
        self.assertEqual(urlparse(cs_request.path).path, "/api/v1/threads/test_id/abuse_flag")
        self.assertEqual(cs_request.method, "PUT")
        self.assertEqual(cs_request.parsed_body, {"user_id": [str(self.user.id)]})

    def test_course_id_missing(self):
        with self.assertRaises(ValidationError) as assertion:
            create_thread(self.request, {})
        self.assertEqual(assertion.exception.message_dict, {"course_id": ["This field is required."]})

    def test_course_id_invalid(self):
        with self.assertRaises(ValidationError) as assertion:
            create_thread(self.request, {"course_id": "invalid!"})
        self.assertEqual(assertion.exception.message_dict, {"course_id": ["Invalid value."]})

    def test_nonexistent_course(self):
        with self.assertRaises(ValidationError) as assertion:
            create_thread(self.request, {"course_id": "non/existent/course"})
        self.assertEqual(assertion.exception.message_dict, {"course_id": ["Invalid value."]})

    def test_not_enrolled(self):
        self.request.user = UserFactory.create()
        with self.assertRaises(ValidationError) as assertion:
            create_thread(self.request, self.minimal_data)
        self.assertEqual(assertion.exception.message_dict, {"course_id": ["Invalid value."]})

    def test_discussions_disabled(self):
        disabled_course = _discussion_disabled_course_for(self.user)
        self.minimal_data["course_id"] = unicode(disabled_course.id)
        with self.assertRaises(ValidationError) as assertion:
            create_thread(self.request, self.minimal_data)
        self.assertEqual(assertion.exception.message_dict, {"course_id": ["Invalid value."]})

    def test_invalid_field(self):
        data = self.minimal_data.copy()
        data["type"] = "invalid_type"
        with self.assertRaises(ValidationError):
            create_thread(self.request, data)


@ddt.ddt
@disable_signal(api, 'comment_created')
@disable_signal(api, 'comment_voted')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class CreateCommentTest(
        CommentsServiceMockMixin,
        UrlResetMixin,
        SharedModuleStoreTestCase,
        MockSignalHandlerMixin
):
    """Tests for create_comment"""
    @classmethod
    def setUpClass(cls):
        super(CreateCommentTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(CreateCommentTest, self).setUp()
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.disable)
        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/test_path")
        self.request.user = self.user
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.register_get_thread_response(
            make_minimal_cs_thread({
                "id": "test_thread",
                "course_id": unicode(self.course.id),
                "commentable_id": "test_topic",
            })
        )
        self.minimal_data = {
            "thread_id": "test_thread",
            "raw_body": "Test body",
        }

    @ddt.data(None, "test_parent")
    @mock.patch("eventtracking.tracker.emit")
    def test_success(self, parent_id, mock_emit):
        if parent_id:
            self.register_get_comment_response({"id": parent_id, "thread_id": "test_thread"})
        self.register_post_comment_response(
            {
                "id": "test_comment",
                "username": self.user.username,
                "created_at": "2015-05-27T00:00:00Z",
                "updated_at": "2015-05-27T00:00:00Z",
            },
            thread_id="test_thread",
            parent_id=parent_id
        )
        data = self.minimal_data.copy()
        if parent_id:
            data["parent_id"] = parent_id
        with self.assert_signal_sent(api, 'comment_created', sender=None, user=self.user, exclude_args=('post',)):
            actual = create_comment(self.request, data)
        expected = {
            "id": "test_comment",
            "thread_id": "test_thread",
            "parent_id": parent_id,
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
            "editable_fields": ["abuse_flagged", "raw_body", "voted"]
        }
        self.assertEqual(actual, expected)
        expected_url = (
            "/api/v1/comments/{}".format(parent_id) if parent_id else
            "/api/v1/threads/test_thread/comments"
        )
        self.assertEqual(
            urlparse(httpretty.last_request().path).path,
            expected_url
        )
        self.assertEqual(
            httpretty.last_request().parsed_body,
            {
                "course_id": [unicode(self.course.id)],
                "body": ["Test body"],
                "user_id": [str(self.user.id)]
            }
        )
        expected_event_name = (
            "edx.forum.comment.created" if parent_id else
            "edx.forum.response.created"
        )
        expected_event_data = {
            "discussion": {"id": "test_thread"},
            "commentable_id": "test_topic",
            "options": {"followed": False},
            "id": "test_comment",
            "truncated": False,
            "body": "Test body",
            "url": "",
            "user_forums_roles": [FORUM_ROLE_STUDENT],
            "user_course_roles": [],
        }
        if parent_id:
            expected_event_data["response"] = {"id": parent_id}
        actual_event_name, actual_event_data = mock_emit.call_args[0]
        self.assertEqual(actual_event_name, expected_event_name)
        self.assertEqual(actual_event_data, expected_event_data)

    @ddt.data(
        *itertools.product(
            [
                FORUM_ROLE_ADMINISTRATOR,
                FORUM_ROLE_MODERATOR,
                FORUM_ROLE_COMMUNITY_TA,
                FORUM_ROLE_STUDENT,
            ],
            [True, False],
            ["question", "discussion"],
        )
    )
    @ddt.unpack
    def test_endorsed(self, role_name, is_thread_author, thread_type):
        role = Role.objects.create(name=role_name, course_id=self.course.id)
        role.users = [self.user]
        self.register_get_thread_response(
            make_minimal_cs_thread({
                "id": "test_thread",
                "course_id": unicode(self.course.id),
                "thread_type": thread_type,
                "user_id": str(self.user.id) if is_thread_author else str(self.user.id + 1),
            })
        )
        self.register_post_comment_response({}, "test_thread")
        data = self.minimal_data.copy()
        data["endorsed"] = True
        expected_error = (
            role_name == FORUM_ROLE_STUDENT and
            (not is_thread_author or thread_type == "discussion")
        )
        try:
            create_comment(self.request, data)
            self.assertEqual(httpretty.last_request().parsed_body["endorsed"], ["True"])
            self.assertFalse(expected_error)
        except ValidationError:
            self.assertTrue(expected_error)

    def test_voted(self):
        self.register_post_comment_response({"id": "test_comment"}, "test_thread")
        self.register_comment_votes_response("test_comment")
        data = self.minimal_data.copy()
        data["voted"] = "True"
        with self.assert_signal_sent(api, 'comment_voted', sender=None, user=self.user, exclude_args=('post',)):
            result = create_comment(self.request, data)
        self.assertEqual(result["voted"], True)
        cs_request = httpretty.last_request()
        self.assertEqual(urlparse(cs_request.path).path, "/api/v1/comments/test_comment/votes")
        self.assertEqual(cs_request.method, "PUT")
        self.assertEqual(
            cs_request.parsed_body,
            {"user_id": [str(self.user.id)], "value": ["up"]}
        )

    def test_abuse_flagged(self):
        self.register_post_comment_response({"id": "test_comment"}, "test_thread")
        self.register_comment_flag_response("test_comment")
        data = self.minimal_data.copy()
        data["abuse_flagged"] = "True"
        result = create_comment(self.request, data)
        self.assertEqual(result["abuse_flagged"], True)
        cs_request = httpretty.last_request()
        self.assertEqual(urlparse(cs_request.path).path, "/api/v1/comments/test_comment/abuse_flag")
        self.assertEqual(cs_request.method, "PUT")
        self.assertEqual(cs_request.parsed_body, {"user_id": [str(self.user.id)]})

    def test_thread_id_missing(self):
        with self.assertRaises(ValidationError) as assertion:
            create_comment(self.request, {})
        self.assertEqual(assertion.exception.message_dict, {"thread_id": ["This field is required."]})

    def test_thread_id_not_found(self):
        self.register_get_thread_error_response("test_thread", 404)
        with self.assertRaises(ValidationError) as assertion:
            create_comment(self.request, self.minimal_data)
        self.assertEqual(assertion.exception.message_dict, {"thread_id": ["Invalid value."]})

    def test_nonexistent_course(self):
        self.register_get_thread_response(
            make_minimal_cs_thread({"id": "test_thread", "course_id": "non/existent/course"})
        )
        with self.assertRaises(ValidationError) as assertion:
            create_comment(self.request, self.minimal_data)
        self.assertEqual(assertion.exception.message_dict, {"thread_id": ["Invalid value."]})

    def test_not_enrolled(self):
        self.request.user = UserFactory.create()
        with self.assertRaises(ValidationError) as assertion:
            create_comment(self.request, self.minimal_data)
        self.assertEqual(assertion.exception.message_dict, {"thread_id": ["Invalid value."]})

    def test_discussions_disabled(self):
        disabled_course = _discussion_disabled_course_for(self.user)
        self.register_get_thread_response(
            make_minimal_cs_thread({
                "id": "test_thread",
                "course_id": unicode(disabled_course.id),
                "commentable_id": "test_topic",
            })
        )
        with self.assertRaises(ValidationError) as assertion:
            create_comment(self.request, self.minimal_data)
        self.assertEqual(assertion.exception.message_dict, {"thread_id": ["Invalid value."]})

    @ddt.data(
        *itertools.product(
            [
                FORUM_ROLE_ADMINISTRATOR,
                FORUM_ROLE_MODERATOR,
                FORUM_ROLE_COMMUNITY_TA,
                FORUM_ROLE_STUDENT,
            ],
            [True, False],
            ["no_group", "match_group", "different_group"],
        )
    )
    @ddt.unpack
    def test_group_access(self, role_name, course_is_cohorted, thread_group_state):
        cohort_course = CourseFactory.create(cohort_config={"cohorted": course_is_cohorted})
        CourseEnrollmentFactory.create(user=self.user, course_id=cohort_course.id)
        cohort = CohortFactory.create(course_id=cohort_course.id, users=[self.user])
        role = Role.objects.create(name=role_name, course_id=cohort_course.id)
        role.users = [self.user]
        self.register_get_thread_response(make_minimal_cs_thread({
            "id": "cohort_thread",
            "course_id": unicode(cohort_course.id),
            "group_id": (
                None if thread_group_state == "no_group" else
                cohort.id if thread_group_state == "match_group" else
                cohort.id + 1
            ),
        }))
        self.register_post_comment_response({}, thread_id="cohort_thread")
        data = self.minimal_data.copy()
        data["thread_id"] = "cohort_thread"
        expected_error = (
            role_name == FORUM_ROLE_STUDENT and
            course_is_cohorted and
            thread_group_state == "different_group"
        )
        try:
            create_comment(self.request, data)
            self.assertFalse(expected_error)
        except ValidationError as err:
            self.assertTrue(expected_error)
            self.assertEqual(
                err.message_dict,
                {"thread_id": ["Invalid value."]}
            )

    def test_invalid_field(self):
        data = self.minimal_data.copy()
        del data["raw_body"]
        with self.assertRaises(ValidationError):
            create_comment(self.request, data)


@ddt.ddt
@disable_signal(api, 'thread_edited')
@disable_signal(api, 'thread_voted')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class UpdateThreadTest(
        CommentsServiceMockMixin,
        UrlResetMixin,
        SharedModuleStoreTestCase,
        MockSignalHandlerMixin
):
    """Tests for update_thread"""
    @classmethod
    def setUpClass(cls):
        super(UpdateThreadTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(UpdateThreadTest, self).setUp()
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.disable)

        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/test_path")
        self.request.user = self.user
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

    def register_thread(self, overrides=None):
        """
        Make a thread with appropriate data overridden by the overrides
        parameter and register mock responses for both GET and PUT on its
        endpoint.
        """
        cs_data = make_minimal_cs_thread({
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
        cs_data.update(overrides or {})
        self.register_get_thread_response(cs_data)
        self.register_put_thread_response(cs_data)

    def test_empty(self):
        """Check that an empty update does not make any modifying requests."""
        # Ensure that the default following value of False is not applied implicitly
        self.register_get_user_response(self.user, subscribed_thread_ids=["test_thread"])
        self.register_thread()
        update_thread(self.request, "test_thread", {})
        for request in httpretty.httpretty.latest_requests:
            self.assertEqual(request.method, "GET")

    def test_basic(self):
        self.register_thread()
        with self.assert_signal_sent(api, 'thread_edited', sender=None, user=self.user, exclude_args=('post',)):
            actual = update_thread(self.request, "test_thread", {"raw_body": "Edited body"})
        expected = {
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
            "comment_count": 1,
            "unread_comment_count": 0,
            "comment_list_url": "http://testserver/api/discussion/v1/comments/?thread_id=test_thread",
            "endorsed_comment_list_url": None,
            "non_endorsed_comment_list_url": None,
            "editable_fields": ["abuse_flagged", "following", "raw_body", "read", "title", "topic_id", "type", "voted"],
            'read': False,
            'has_endorsed': False,
            'response_count': 0
        }
        self.assertEqual(actual, expected)
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

    def test_nonexistent_thread(self):
        self.register_get_thread_error_response("test_thread", 404)
        with self.assertRaises(Http404):
            update_thread(self.request, "test_thread", {})

    def test_nonexistent_course(self):
        self.register_thread({"course_id": "non/existent/course"})
        with self.assertRaises(Http404):
            update_thread(self.request, "test_thread", {})

    def test_not_enrolled(self):
        self.register_thread()
        self.request.user = UserFactory.create()
        with self.assertRaises(Http404):
            update_thread(self.request, "test_thread", {})

    def test_discussions_disabled(self):
        disabled_course = _discussion_disabled_course_for(self.user)
        self.register_thread(overrides={"course_id": unicode(disabled_course.id)})
        with self.assertRaises(Http404):
            update_thread(self.request, "test_thread", {})

    @ddt.data(
        *itertools.product(
            [
                FORUM_ROLE_ADMINISTRATOR,
                FORUM_ROLE_MODERATOR,
                FORUM_ROLE_COMMUNITY_TA,
                FORUM_ROLE_STUDENT,
            ],
            [True, False],
            ["no_group", "match_group", "different_group"],
        )
    )
    @ddt.unpack
    def test_group_access(self, role_name, course_is_cohorted, thread_group_state):
        cohort_course = CourseFactory.create(cohort_config={"cohorted": course_is_cohorted})
        CourseEnrollmentFactory.create(user=self.user, course_id=cohort_course.id)
        cohort = CohortFactory.create(course_id=cohort_course.id, users=[self.user])
        role = Role.objects.create(name=role_name, course_id=cohort_course.id)
        role.users = [self.user]
        self.register_thread({
            "course_id": unicode(cohort_course.id),
            "group_id": (
                None if thread_group_state == "no_group" else
                cohort.id if thread_group_state == "match_group" else
                cohort.id + 1
            ),
        })
        expected_error = (
            role_name == FORUM_ROLE_STUDENT and
            course_is_cohorted and
            thread_group_state == "different_group"
        )
        try:
            update_thread(self.request, "test_thread", {})
            self.assertFalse(expected_error)
        except Http404:
            self.assertTrue(expected_error)

    @ddt.data(
        FORUM_ROLE_ADMINISTRATOR,
        FORUM_ROLE_MODERATOR,
        FORUM_ROLE_COMMUNITY_TA,
        FORUM_ROLE_STUDENT,
    )
    def test_author_only_fields(self, role_name):
        role = Role.objects.create(name=role_name, course_id=self.course.id)
        role.users = [self.user]
        self.register_thread({"user_id": str(self.user.id + 1)})
        data = {field: "edited" for field in ["topic_id", "title", "raw_body"]}
        data["type"] = "question"
        expected_error = role_name == FORUM_ROLE_STUDENT
        try:
            update_thread(self.request, "test_thread", data)
            self.assertFalse(expected_error)
        except ValidationError as err:
            self.assertTrue(expected_error)
            self.assertEqual(
                err.message_dict,
                {field: ["This field is not editable."] for field in data.keys()}
            )

    @ddt.data(*itertools.product([True, False], [True, False]))
    @ddt.unpack
    def test_following(self, old_following, new_following):
        """
        Test attempts to edit the "following" field.

        old_following indicates whether the thread should be followed at the
        start of the test. new_following indicates the value for the "following"
        field in the update. If old_following and new_following are the same, no
        update should be made. Otherwise, a subscription should be POSTed or
        DELETEd according to the new_following value.
        """
        if old_following:
            self.register_get_user_response(self.user, subscribed_thread_ids=["test_thread"])
        self.register_subscription_response(self.user)
        self.register_thread()
        data = {"following": new_following}
        result = update_thread(self.request, "test_thread", data)
        self.assertEqual(result["following"], new_following)
        last_request_path = urlparse(httpretty.last_request().path).path
        subscription_url = "/api/v1/users/{}/subscriptions".format(self.user.id)
        if old_following == new_following:
            self.assertNotEqual(last_request_path, subscription_url)
        else:
            self.assertEqual(last_request_path, subscription_url)
            self.assertEqual(
                httpretty.last_request().method,
                "POST" if new_following else "DELETE"
            )
            request_data = (
                httpretty.last_request().parsed_body if new_following else
                parse_qs(urlparse(httpretty.last_request().path).query)
            )
            request_data.pop("request_id", None)
            self.assertEqual(
                request_data,
                {"source_type": ["thread"], "source_id": ["test_thread"]}
            )

    @ddt.data(*itertools.product([True, False], [True, False]))
    @ddt.unpack
    def test_voted(self, current_vote_status, new_vote_status):
        """
        Test attempts to edit the "voted" field.

        current_vote_status indicates whether the thread should be upvoted at
        the start of the test. new_vote_status indicates the value for the
        "voted" field in the update. If current_vote_status and new_vote_status
        are the same, no update should be made. Otherwise, a vote should be PUT
        or DELETEd according to the new_vote_status value.
        """
        if current_vote_status:
            self.register_get_user_response(self.user, upvoted_ids=["test_thread"])
        self.register_thread_votes_response("test_thread")
        self.register_thread()
        data = {"voted": new_vote_status}
        result = update_thread(self.request, "test_thread", data)
        self.assertEqual(result["voted"], new_vote_status)
        last_request_path = urlparse(httpretty.last_request().path).path
        votes_url = "/api/v1/threads/test_thread/votes"
        if current_vote_status == new_vote_status:
            self.assertNotEqual(last_request_path, votes_url)
        else:
            self.assertEqual(last_request_path, votes_url)
            self.assertEqual(
                httpretty.last_request().method,
                "PUT" if new_vote_status else "DELETE"
            )
            actual_request_data = (
                httpretty.last_request().parsed_body if new_vote_status else
                parse_qs(urlparse(httpretty.last_request().path).query)
            )
            actual_request_data.pop("request_id", None)
            expected_request_data = {"user_id": [str(self.user.id)]}
            if new_vote_status:
                expected_request_data["value"] = ["up"]
            self.assertEqual(actual_request_data, expected_request_data)

    @ddt.data(*itertools.product([True, False], [True, False], [True, False]))
    @ddt.unpack
    def test_vote_count(self, current_vote_status, first_vote, second_vote):
        """
        Tests vote_count increases and decreases correctly from the same user
        """
        #setup
        starting_vote_count = 0
        if current_vote_status:
            self.register_get_user_response(self.user, upvoted_ids=["test_thread"])
            starting_vote_count = 1
        self.register_thread_votes_response("test_thread")
        self.register_thread(overrides={"votes": {"up_count": starting_vote_count}})

        #first vote
        data = {"voted": first_vote}
        result = update_thread(self.request, "test_thread", data)
        self.register_thread(overrides={"voted": first_vote})
        self.assertEqual(result["vote_count"], 1 if first_vote else 0)

        #second vote
        data = {"voted": second_vote}
        result = update_thread(self.request, "test_thread", data)
        self.assertEqual(result["vote_count"], 1 if second_vote else 0)

    @ddt.data(*itertools.product([True, False], [True, False], [True, False], [True, False]))
    @ddt.unpack
    def test_vote_count_two_users(
            self,
            current_user1_vote,
            current_user2_vote,
            user1_vote,
            user2_vote
    ):
        """
        Tests vote_count increases and decreases correctly from different users
        """
        #setup
        user2 = UserFactory.create()
        self.register_get_user_response(user2)
        request2 = RequestFactory().get("/test_path")
        request2.user = user2
        CourseEnrollmentFactory.create(user=user2, course_id=self.course.id)

        vote_count = 0
        if current_user1_vote:
            self.register_get_user_response(self.user, upvoted_ids=["test_thread"])
            vote_count += 1
        if current_user2_vote:
            self.register_get_user_response(user2, upvoted_ids=["test_thread"])
            vote_count += 1

        for (current_vote, user_vote, request) in \
                [(current_user1_vote, user1_vote, self.request),
                 (current_user2_vote, user2_vote, request2)]:

            self.register_thread_votes_response("test_thread")
            self.register_thread(overrides={"votes": {"up_count": vote_count}})

            data = {"voted": user_vote}
            result = update_thread(request, "test_thread", data)
            if current_vote == user_vote:
                self.assertEqual(result["vote_count"], vote_count)
            elif user_vote:
                vote_count += 1
                self.assertEqual(result["vote_count"], vote_count)
                self.register_get_user_response(self.user, upvoted_ids=["test_thread"])
            else:
                vote_count -= 1
                self.assertEqual(result["vote_count"], vote_count)
                self.register_get_user_response(self.user, upvoted_ids=[])

    @ddt.data(*itertools.product([True, False], [True, False]))
    @ddt.unpack
    def test_abuse_flagged(self, old_flagged, new_flagged):
        """
        Test attempts to edit the "abuse_flagged" field.

        old_flagged indicates whether the thread should be flagged at the start
        of the test. new_flagged indicates the value for the "abuse_flagged"
        field in the update. If old_flagged and new_flagged are the same, no
        update should be made. Otherwise, a PUT should be made to the flag or
        or unflag endpoint according to the new_flagged value.
        """
        self.register_get_user_response(self.user)
        self.register_thread_flag_response("test_thread")
        self.register_thread({"abuse_flaggers": [str(self.user.id)] if old_flagged else []})
        data = {"abuse_flagged": new_flagged}
        result = update_thread(self.request, "test_thread", data)
        self.assertEqual(result["abuse_flagged"], new_flagged)
        last_request_path = urlparse(httpretty.last_request().path).path
        flag_url = "/api/v1/threads/test_thread/abuse_flag"
        unflag_url = "/api/v1/threads/test_thread/abuse_unflag"
        if old_flagged == new_flagged:
            self.assertNotEqual(last_request_path, flag_url)
            self.assertNotEqual(last_request_path, unflag_url)
        else:
            self.assertEqual(
                last_request_path,
                flag_url if new_flagged else unflag_url
            )
            self.assertEqual(httpretty.last_request().method, "PUT")
            self.assertEqual(
                httpretty.last_request().parsed_body,
                {"user_id": [str(self.user.id)]}
            )

    def test_invalid_field(self):
        self.register_thread()
        with self.assertRaises(ValidationError) as assertion:
            update_thread(self.request, "test_thread", {"raw_body": ""})
        self.assertEqual(
            assertion.exception.message_dict,
            {"raw_body": ["This field may not be blank."]}
        )


@ddt.ddt
@disable_signal(api, 'comment_edited')
@disable_signal(api, 'comment_voted')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class UpdateCommentTest(
        CommentsServiceMockMixin,
        UrlResetMixin,
        SharedModuleStoreTestCase,
        MockSignalHandlerMixin
):
    """Tests for update_comment"""

    @classmethod
    def setUpClass(cls):
        super(UpdateCommentTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(UpdateCommentTest, self).setUp()

        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.disable)

        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/test_path")
        self.request.user = self.user
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

    def register_comment(self, overrides=None, thread_overrides=None, course=None):
        """
        Make a comment with appropriate data overridden by the overrides
        parameter and register mock responses for both GET and PUT on its
        endpoint. Also mock GET for the related thread with thread_overrides.
        """
        if course is None:
            course = self.course

        cs_thread_data = make_minimal_cs_thread({
            "id": "test_thread",
            "course_id": unicode(course.id)
        })
        cs_thread_data.update(thread_overrides or {})
        self.register_get_thread_response(cs_thread_data)
        cs_comment_data = make_minimal_cs_comment({
            "id": "test_comment",
            "course_id": cs_thread_data["course_id"],
            "thread_id": cs_thread_data["id"],
            "username": self.user.username,
            "user_id": str(self.user.id),
            "created_at": "2015-06-03T00:00:00Z",
            "updated_at": "2015-06-03T00:00:00Z",
            "body": "Original body",
        })
        cs_comment_data.update(overrides or {})
        self.register_get_comment_response(cs_comment_data)
        self.register_put_comment_response(cs_comment_data)

    def test_empty(self):
        """Check that an empty update does not make any modifying requests."""
        self.register_comment()
        update_comment(self.request, "test_comment", {})
        for request in httpretty.httpretty.latest_requests:
            self.assertEqual(request.method, "GET")

    @ddt.data(None, "test_parent")
    def test_basic(self, parent_id):
        self.register_comment({"parent_id": parent_id})
        with self.assert_signal_sent(api, 'comment_edited', sender=None, user=self.user, exclude_args=('post',)):
            actual = update_comment(self.request, "test_comment", {"raw_body": "Edited body"})
        expected = {
            "id": "test_comment",
            "thread_id": "test_thread",
            "parent_id": parent_id,
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
            "editable_fields": ["abuse_flagged", "raw_body", "voted"]
        }
        self.assertEqual(actual, expected)
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

    def test_nonexistent_comment(self):
        self.register_get_comment_error_response("test_comment", 404)
        with self.assertRaises(Http404):
            update_comment(self.request, "test_comment", {})

    def test_nonexistent_course(self):
        self.register_comment(thread_overrides={"course_id": "non/existent/course"})
        with self.assertRaises(Http404):
            update_comment(self.request, "test_comment", {})

    def test_unenrolled(self):
        self.register_comment()
        self.request.user = UserFactory.create()
        with self.assertRaises(Http404):
            update_comment(self.request, "test_comment", {})

    def test_discussions_disabled(self):
        self.register_comment(course=_discussion_disabled_course_for(self.user))
        with self.assertRaises(Http404):
            update_comment(self.request, "test_comment", {})

    @ddt.data(
        *itertools.product(
            [
                FORUM_ROLE_ADMINISTRATOR,
                FORUM_ROLE_MODERATOR,
                FORUM_ROLE_COMMUNITY_TA,
                FORUM_ROLE_STUDENT,
            ],
            [True, False],
            ["no_group", "match_group", "different_group"],
        )
    )
    @ddt.unpack
    def test_group_access(self, role_name, course_is_cohorted, thread_group_state):
        cohort_course = CourseFactory.create(cohort_config={"cohorted": course_is_cohorted})
        CourseEnrollmentFactory.create(user=self.user, course_id=cohort_course.id)
        cohort = CohortFactory.create(course_id=cohort_course.id, users=[self.user])
        role = Role.objects.create(name=role_name, course_id=cohort_course.id)
        role.users = [self.user]
        self.register_get_thread_response(make_minimal_cs_thread())
        self.register_comment(
            {"thread_id": "test_thread"},
            thread_overrides={
                "id": "test_thread",
                "course_id": unicode(cohort_course.id),
                "group_id": (
                    None if thread_group_state == "no_group" else
                    cohort.id if thread_group_state == "match_group" else
                    cohort.id + 1
                ),
            }
        )
        expected_error = (
            role_name == FORUM_ROLE_STUDENT and
            course_is_cohorted and
            thread_group_state == "different_group"
        )
        try:
            update_comment(self.request, "test_comment", {})
            self.assertFalse(expected_error)
        except Http404:
            self.assertTrue(expected_error)

    @ddt.data(*itertools.product(
        [
            FORUM_ROLE_ADMINISTRATOR,
            FORUM_ROLE_MODERATOR,
            FORUM_ROLE_COMMUNITY_TA,
            FORUM_ROLE_STUDENT,
        ],
        [True, False],
        [True, False],
    ))
    @ddt.unpack
    def test_raw_body_access(self, role_name, is_thread_author, is_comment_author):
        role = Role.objects.create(name=role_name, course_id=self.course.id)
        role.users = [self.user]
        self.register_comment(
            {"user_id": str(self.user.id if is_comment_author else (self.user.id + 1))},
            thread_overrides={
                "user_id": str(self.user.id if is_thread_author else (self.user.id + 1))
            }
        )
        expected_error = role_name == FORUM_ROLE_STUDENT and not is_comment_author
        try:
            update_comment(self.request, "test_comment", {"raw_body": "edited"})
            self.assertFalse(expected_error)
        except ValidationError as err:
            self.assertTrue(expected_error)
            self.assertEqual(
                err.message_dict,
                {"raw_body": ["This field is not editable."]}
            )

    @ddt.data(*itertools.product(
        [
            FORUM_ROLE_ADMINISTRATOR,
            FORUM_ROLE_MODERATOR,
            FORUM_ROLE_COMMUNITY_TA,
            FORUM_ROLE_STUDENT,
        ],
        [True, False],
        ["question", "discussion"],
        [True, False],
    ))
    @ddt.unpack
    def test_endorsed_access(self, role_name, is_thread_author, thread_type, is_comment_author):
        role = Role.objects.create(name=role_name, course_id=self.course.id)
        role.users = [self.user]
        self.register_comment(
            {"user_id": str(self.user.id if is_comment_author else (self.user.id + 1))},
            thread_overrides={
                "thread_type": thread_type,
                "user_id": str(self.user.id if is_thread_author else (self.user.id + 1)),
            }
        )
        expected_error = (
            role_name == FORUM_ROLE_STUDENT and
            (thread_type == "discussion" or not is_thread_author)
        )
        try:
            update_comment(self.request, "test_comment", {"endorsed": True})
            self.assertFalse(expected_error)
        except ValidationError as err:
            self.assertTrue(expected_error)
            self.assertEqual(
                err.message_dict,
                {"endorsed": ["This field is not editable."]}
            )

    @ddt.data(*itertools.product([True, False], [True, False]))
    @ddt.unpack
    def test_voted(self, current_vote_status, new_vote_status):
        """
        Test attempts to edit the "voted" field.

        current_vote_status indicates whether the comment should be upvoted at
        the start of the test. new_vote_status indicates the value for the
        "voted" field in the update. If current_vote_status and new_vote_status
        are the same, no update should be made. Otherwise, a vote should be PUT
        or DELETEd according to the new_vote_status value.
        """
        vote_count = 0
        if current_vote_status:
            self.register_get_user_response(self.user, upvoted_ids=["test_comment"])
            vote_count = 1
        self.register_comment_votes_response("test_comment")
        self.register_comment(overrides={"votes": {"up_count": vote_count}})
        data = {"voted": new_vote_status}
        result = update_comment(self.request, "test_comment", data)
        self.assertEqual(result["vote_count"], 1 if new_vote_status else 0)
        self.assertEqual(result["voted"], new_vote_status)
        last_request_path = urlparse(httpretty.last_request().path).path
        votes_url = "/api/v1/comments/test_comment/votes"
        if current_vote_status == new_vote_status:
            self.assertNotEqual(last_request_path, votes_url)
        else:
            self.assertEqual(last_request_path, votes_url)
            self.assertEqual(
                httpretty.last_request().method,
                "PUT" if new_vote_status else "DELETE"
            )
            actual_request_data = (
                httpretty.last_request().parsed_body if new_vote_status else
                parse_qs(urlparse(httpretty.last_request().path).query)
            )
            actual_request_data.pop("request_id", None)
            expected_request_data = {"user_id": [str(self.user.id)]}
            if new_vote_status:
                expected_request_data["value"] = ["up"]
            self.assertEqual(actual_request_data, expected_request_data)

    @ddt.data(*itertools.product([True, False], [True, False], [True, False]))
    @ddt.unpack
    def test_vote_count(self, current_vote_status, first_vote, second_vote):
        """
        Tests vote_count increases and decreases correctly from the same user
        """
        #setup
        starting_vote_count = 0
        if current_vote_status:
            self.register_get_user_response(self.user, upvoted_ids=["test_comment"])
            starting_vote_count = 1
        self.register_comment_votes_response("test_comment")
        self.register_comment(overrides={"votes": {"up_count": starting_vote_count}})

        #first vote
        data = {"voted": first_vote}
        result = update_comment(self.request, "test_comment", data)
        self.register_comment(overrides={"voted": first_vote})
        self.assertEqual(result["vote_count"], 1 if first_vote else 0)

        #second vote
        data = {"voted": second_vote}
        result = update_comment(self.request, "test_comment", data)
        self.assertEqual(result["vote_count"], 1 if second_vote else 0)

    @ddt.data(*itertools.product([True, False], [True, False], [True, False], [True, False]))
    @ddt.unpack
    def test_vote_count_two_users(
            self,
            current_user1_vote,
            current_user2_vote,
            user1_vote,
            user2_vote
    ):
        """
        Tests vote_count increases and decreases correctly from different users
        """
        user2 = UserFactory.create()
        self.register_get_user_response(user2)
        request2 = RequestFactory().get("/test_path")
        request2.user = user2
        CourseEnrollmentFactory.create(user=user2, course_id=self.course.id)

        vote_count = 0
        if current_user1_vote:
            self.register_get_user_response(self.user, upvoted_ids=["test_comment"])
            vote_count += 1
        if current_user2_vote:
            self.register_get_user_response(user2, upvoted_ids=["test_comment"])
            vote_count += 1

        for (current_vote, user_vote, request) in \
                [(current_user1_vote, user1_vote, self.request),
                 (current_user2_vote, user2_vote, request2)]:

            self.register_comment_votes_response("test_comment")
            self.register_comment(overrides={"votes": {"up_count": vote_count}})

            data = {"voted": user_vote}
            result = update_comment(request, "test_comment", data)
            if current_vote == user_vote:
                self.assertEqual(result["vote_count"], vote_count)
            elif user_vote:
                vote_count += 1
                self.assertEqual(result["vote_count"], vote_count)
                self.register_get_user_response(self.user, upvoted_ids=["test_comment"])
            else:
                vote_count -= 1
                self.assertEqual(result["vote_count"], vote_count)
                self.register_get_user_response(self.user, upvoted_ids=[])

    @ddt.data(*itertools.product([True, False], [True, False]))
    @ddt.unpack
    def test_abuse_flagged(self, old_flagged, new_flagged):
        """
        Test attempts to edit the "abuse_flagged" field.

        old_flagged indicates whether the comment should be flagged at the start
        of the test. new_flagged indicates the value for the "abuse_flagged"
        field in the update. If old_flagged and new_flagged are the same, no
        update should be made. Otherwise, a PUT should be made to the flag or
        or unflag endpoint according to the new_flagged value.
        """
        self.register_get_user_response(self.user)
        self.register_comment_flag_response("test_comment")
        self.register_comment({"abuse_flaggers": [str(self.user.id)] if old_flagged else []})
        data = {"abuse_flagged": new_flagged}
        result = update_comment(self.request, "test_comment", data)
        self.assertEqual(result["abuse_flagged"], new_flagged)
        last_request_path = urlparse(httpretty.last_request().path).path
        flag_url = "/api/v1/comments/test_comment/abuse_flag"
        unflag_url = "/api/v1/comments/test_comment/abuse_unflag"
        if old_flagged == new_flagged:
            self.assertNotEqual(last_request_path, flag_url)
            self.assertNotEqual(last_request_path, unflag_url)
        else:
            self.assertEqual(
                last_request_path,
                flag_url if new_flagged else unflag_url
            )
            self.assertEqual(httpretty.last_request().method, "PUT")
            self.assertEqual(
                httpretty.last_request().parsed_body,
                {"user_id": [str(self.user.id)]}
            )


@ddt.ddt
@disable_signal(api, 'thread_deleted')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class DeleteThreadTest(
        CommentsServiceMockMixin,
        UrlResetMixin,
        SharedModuleStoreTestCase,
        MockSignalHandlerMixin
):
    """Tests for delete_thread"""
    @classmethod
    def setUpClass(cls):
        super(DeleteThreadTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(DeleteThreadTest, self).setUp()
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.disable)
        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/test_path")
        self.request.user = self.user
        self.thread_id = "test_thread"
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

    def register_thread(self, overrides=None):
        """
        Make a thread with appropriate data overridden by the overrides
        parameter and register mock responses for both GET and DELETE on its
        endpoint.
        """
        cs_data = make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": unicode(self.course.id),
            "user_id": str(self.user.id),
        })
        cs_data.update(overrides or {})
        self.register_get_thread_response(cs_data)
        self.register_delete_thread_response(cs_data["id"])

    def test_basic(self):
        self.register_thread()
        with self.assert_signal_sent(api, 'thread_deleted', sender=None, user=self.user, exclude_args=('post',)):
            self.assertIsNone(delete_thread(self.request, self.thread_id))
        self.assertEqual(
            urlparse(httpretty.last_request().path).path,
            "/api/v1/threads/{}".format(self.thread_id)
        )
        self.assertEqual(httpretty.last_request().method, "DELETE")

    def test_thread_id_not_found(self):
        self.register_get_thread_error_response("missing_thread", 404)
        with self.assertRaises(Http404):
            delete_thread(self.request, "missing_thread")

    def test_nonexistent_course(self):
        self.register_thread({"course_id": "non/existent/course"})
        with self.assertRaises(Http404):
            delete_thread(self.request, self.thread_id)

    def test_not_enrolled(self):
        self.register_thread()
        self.request.user = UserFactory.create()
        with self.assertRaises(Http404):
            delete_thread(self.request, self.thread_id)

    def test_discussions_disabled(self):
        disabled_course = _discussion_disabled_course_for(self.user)
        self.register_thread(overrides={"course_id": unicode(disabled_course.id)})
        with self.assertRaises(Http404):
            delete_thread(self.request, self.thread_id)

    @ddt.data(
        FORUM_ROLE_ADMINISTRATOR,
        FORUM_ROLE_MODERATOR,
        FORUM_ROLE_COMMUNITY_TA,
        FORUM_ROLE_STUDENT,
    )
    def test_non_author_delete_allowed(self, role_name):
        role = Role.objects.create(name=role_name, course_id=self.course.id)
        role.users = [self.user]
        self.register_thread({"user_id": str(self.user.id + 1)})
        expected_error = role_name == FORUM_ROLE_STUDENT
        try:
            delete_thread(self.request, self.thread_id)
            self.assertFalse(expected_error)
        except PermissionDenied:
            self.assertTrue(expected_error)

    @ddt.data(
        *itertools.product(
            [
                FORUM_ROLE_ADMINISTRATOR,
                FORUM_ROLE_MODERATOR,
                FORUM_ROLE_COMMUNITY_TA,
                FORUM_ROLE_STUDENT,
            ],
            [True, False],
            ["no_group", "match_group", "different_group"],
        )
    )
    @ddt.unpack
    def test_group_access(self, role_name, course_is_cohorted, thread_group_state):
        """
        Tests group access for deleting a thread

        All privileged roles are able to delete a thread. A student role can
        only delete a thread if,
        the student role is the author and the thread is not in a cohort,
        the student role is the author and the thread is in the author's cohort.
        """
        cohort_course = CourseFactory.create(cohort_config={"cohorted": course_is_cohorted})
        CourseEnrollmentFactory.create(user=self.user, course_id=cohort_course.id)
        cohort = CohortFactory.create(course_id=cohort_course.id, users=[self.user])
        role = Role.objects.create(name=role_name, course_id=cohort_course.id)
        role.users = [self.user]
        self.register_thread({
            "course_id": unicode(cohort_course.id),
            "group_id": (
                None if thread_group_state == "no_group" else
                cohort.id if thread_group_state == "match_group" else
                cohort.id + 1
            ),
        })
        expected_error = (
            role_name == FORUM_ROLE_STUDENT and
            course_is_cohorted and
            thread_group_state == "different_group"
        )
        try:
            delete_thread(self.request, self.thread_id)
            self.assertFalse(expected_error)
        except Http404:
            self.assertTrue(expected_error)


@ddt.ddt
@disable_signal(api, 'comment_deleted')
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class DeleteCommentTest(
        CommentsServiceMockMixin,
        UrlResetMixin,
        SharedModuleStoreTestCase,
        MockSignalHandlerMixin
):
    """Tests for delete_comment"""
    @classmethod
    def setUpClass(cls):
        super(DeleteCommentTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(DeleteCommentTest, self).setUp()
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.disable)
        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/test_path")
        self.request.user = self.user
        self.thread_id = "test_thread"
        self.comment_id = "test_comment"
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

    def register_comment_and_thread(self, overrides=None, thread_overrides=None):
        """
        Make a comment with appropriate data overridden by the override
        parameters and register mock responses for both GET and DELETE on its
        endpoint. Also mock GET for the related thread with thread_overrides.
        """
        cs_thread_data = make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": unicode(self.course.id)
        })
        cs_thread_data.update(thread_overrides or {})
        self.register_get_thread_response(cs_thread_data)
        cs_comment_data = make_minimal_cs_comment({
            "id": self.comment_id,
            "course_id": cs_thread_data["course_id"],
            "thread_id": cs_thread_data["id"],
            "username": self.user.username,
            "user_id": str(self.user.id),
        })
        cs_comment_data.update(overrides or {})
        self.register_get_comment_response(cs_comment_data)
        self.register_delete_comment_response(self.comment_id)

    def test_basic(self):
        self.register_comment_and_thread()
        with self.assert_signal_sent(api, 'comment_deleted', sender=None, user=self.user, exclude_args=('post',)):
            self.assertIsNone(delete_comment(self.request, self.comment_id))
        self.assertEqual(
            urlparse(httpretty.last_request().path).path,
            "/api/v1/comments/{}".format(self.comment_id)
        )
        self.assertEqual(httpretty.last_request().method, "DELETE")

    def test_comment_id_not_found(self):
        self.register_get_comment_error_response("missing_comment", 404)
        with self.assertRaises(Http404):
            delete_comment(self.request, "missing_comment")

    def test_nonexistent_course(self):
        self.register_comment_and_thread(
            thread_overrides={"course_id": "non/existent/course"}
        )
        with self.assertRaises(Http404):
            delete_comment(self.request, self.comment_id)

    def test_not_enrolled(self):
        self.register_comment_and_thread()
        self.request.user = UserFactory.create()
        with self.assertRaises(Http404):
            delete_comment(self.request, self.comment_id)

    def test_discussions_disabled(self):
        disabled_course = _discussion_disabled_course_for(self.user)
        self.register_comment_and_thread(
            thread_overrides={"course_id": unicode(disabled_course.id)},
            overrides={"course_id": unicode(disabled_course.id)}
        )
        with self.assertRaises(Http404):
            delete_comment(self.request, self.comment_id)

    @ddt.data(
        FORUM_ROLE_ADMINISTRATOR,
        FORUM_ROLE_MODERATOR,
        FORUM_ROLE_COMMUNITY_TA,
        FORUM_ROLE_STUDENT,
    )
    def test_non_author_delete_allowed(self, role_name):
        role = Role.objects.create(name=role_name, course_id=self.course.id)
        role.users = [self.user]
        self.register_comment_and_thread(
            overrides={"user_id": str(self.user.id + 1)}
        )
        expected_error = role_name == FORUM_ROLE_STUDENT
        try:
            delete_comment(self.request, self.comment_id)
            self.assertFalse(expected_error)
        except PermissionDenied:
            self.assertTrue(expected_error)

    @ddt.data(
        *itertools.product(
            [
                FORUM_ROLE_ADMINISTRATOR,
                FORUM_ROLE_MODERATOR,
                FORUM_ROLE_COMMUNITY_TA,
                FORUM_ROLE_STUDENT,
            ],
            [True, False],
            ["no_group", "match_group", "different_group"],
        )
    )
    @ddt.unpack
    def test_group_access(self, role_name, course_is_cohorted, thread_group_state):
        """
        Tests group access for deleting a comment

        All privileged roles are able to delete a comment. A student role can
        only delete a comment if,
        the student role is the author and the comment is not in a cohort,
        the student role is the author and the comment is in the author's cohort.
        """
        cohort_course = CourseFactory.create(cohort_config={"cohorted": course_is_cohorted})
        CourseEnrollmentFactory.create(user=self.user, course_id=cohort_course.id)
        cohort = CohortFactory.create(course_id=cohort_course.id, users=[self.user])
        role = Role.objects.create(name=role_name, course_id=cohort_course.id)
        role.users = [self.user]
        self.register_comment_and_thread(
            overrides={"thread_id": "test_thread"},
            thread_overrides={
                "course_id": unicode(cohort_course.id),
                "group_id": (
                    None if thread_group_state == "no_group" else
                    cohort.id if thread_group_state == "match_group" else
                    cohort.id + 1
                ),
            }
        )
        expected_error = (
            role_name == FORUM_ROLE_STUDENT and
            course_is_cohorted and
            thread_group_state == "different_group"
        )
        try:
            delete_comment(self.request, self.comment_id)
            self.assertFalse(expected_error)
        except Http404:
            self.assertTrue(expected_error)


@ddt.ddt
@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class RetrieveThreadTest(
        CommentsServiceMockMixin,
        UrlResetMixin,
        SharedModuleStoreTestCase
):
    """Tests for get_thread"""
    @classmethod
    def setUpClass(cls):
        super(RetrieveThreadTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(RetrieveThreadTest, self).setUp()
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.disable)
        self.thread_author = UserFactory.create()
        self.register_get_user_response(self.thread_author)
        self.request = RequestFactory().get("/test_path")
        self.request.user = self.thread_author
        self.thread_id = "test_thread"
        CourseEnrollmentFactory.create(user=self.thread_author, course_id=self.course.id)

    def register_thread(self, overrides=None):
        """
        Make a thread with appropriate data overridden by the overrides
        parameter and register mock responses for GET on its
        endpoint.
        """
        cs_data = make_minimal_cs_thread({
            "id": self.thread_id,
            "course_id": unicode(self.course.id),
            "commentable_id": "test_topic",
            "username": self.thread_author.username,
            "user_id": str(self.thread_author.id),
            "title": "Test Title",
            "body": "Test body",
            "created_at": "2015-05-29T00:00:00Z",
            "updated_at": "2015-05-29T00:00:00Z",
            "resp_total": 0,

        })
        cs_data.update(overrides or {})
        self.register_get_thread_response(cs_data)

    def test_basic(self):
        expected_response_data = {
            "author": self.thread_author.username,
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
            "response_count": 2,
        }
        self.register_thread({"resp_total": 2})
        self.assertEqual(get_thread(self.request, self.thread_id), expected_response_data)
        self.assertEqual(httpretty.last_request().method, "GET")

    def test_thread_id_not_found(self):
        self.register_get_thread_error_response("missing_thread", 404)
        with self.assertRaises(Http404):
            get_thread(self.request, "missing_thread")

    def test_nonauthor_enrolled_in_course(self):
        expected_response_data = {
            "author": self.thread_author.username,
            "author_label": None,
            "created_at": "2015-05-29T00:00:00Z",
            "updated_at": "2015-05-29T00:00:00Z",
            "raw_body": "Test body",
            "rendered_body": "<p>Test body</p>",
            "abuse_flagged": False,
            "voted": False,
            "vote_count": 0,
            "editable_fields": ["abuse_flagged", "following", "read", "voted"],
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
        non_author_user = UserFactory.create()
        self.register_get_user_response(non_author_user)
        CourseEnrollmentFactory.create(user=non_author_user, course_id=self.course.id)
        self.register_thread()
        self.request.user = non_author_user
        self.assertEqual(get_thread(self.request, self.thread_id), expected_response_data)
        self.assertEqual(httpretty.last_request().method, "GET")

    def test_not_enrolled_in_course(self):
        self.register_thread()
        self.request.user = UserFactory.create()
        with self.assertRaises(Http404):
            get_thread(self.request, self.thread_id)

    @ddt.data(
        *itertools.product(
            [
                FORUM_ROLE_ADMINISTRATOR,
                FORUM_ROLE_MODERATOR,
                FORUM_ROLE_COMMUNITY_TA,
                FORUM_ROLE_STUDENT,
            ],
            [True, False],
            ["no_group", "match_group", "different_group"],
        )
    )
    @ddt.unpack
    def test_group_access(self, role_name, course_is_cohorted, thread_group_state):
        """
        Tests group access for retrieving a thread

        All privileged roles are able to retrieve a thread. A student role can
        only retrieve a thread if,
        the student role is the author and the thread is not in a cohort,
        the student role is the author and the thread is in the author's cohort.
        """
        cohort_course = CourseFactory.create(cohort_config={"cohorted": course_is_cohorted})
        CourseEnrollmentFactory.create(user=self.thread_author, course_id=cohort_course.id)
        cohort = CohortFactory.create(course_id=cohort_course.id, users=[self.thread_author])
        role = Role.objects.create(name=role_name, course_id=cohort_course.id)
        role.users = [self.thread_author]
        self.register_thread({
            "course_id": unicode(cohort_course.id),
            "group_id": (
                None if thread_group_state == "no_group" else
                cohort.id if thread_group_state == "match_group" else
                cohort.id + 1
            ),
        })
        expected_error = (
            role_name == FORUM_ROLE_STUDENT and
            course_is_cohorted and
            thread_group_state == "different_group"
        )
        try:
            get_thread(self.request, self.thread_id)
            self.assertFalse(expected_error)
        except Http404:
            self.assertTrue(expected_error)
