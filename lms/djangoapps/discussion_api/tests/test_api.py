"""
Tests for Discussion API internal interface
"""
from datetime import datetime, timedelta
import itertools

import ddt
import httpretty
import mock
from pytz import UTC

from django.http import Http404
from django.test.client import RequestFactory

from opaque_keys.edx.locator import CourseLocator

from courseware.tests.factories import BetaTesterFactory, StaffFactory
from discussion_api.api import get_course_topics, get_thread_list
from discussion_api.tests.utils import CommentsServiceMockMixin
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
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.partitions.partitions import Group, UserPartition
from xmodule.tabs import DiscussionTab


def _remove_discussion_tab(course, user_id):
    """
    Remove the discussion tab for the course.

    user_id is passed to the modulestore as the editor of the module.
    """
    course.tabs = [tab for tab in course.tabs if not isinstance(tab, DiscussionTab)]
    modulestore().update_item(course, user_id)


@mock.patch.dict("django.conf.settings.FEATURES", {"DISABLE_START_DATES": False})
class GetCourseTopicsTest(ModuleStoreTestCase):
    """Test for get_course_topics"""

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

    def get_course_topics(self, user=None):
        """
        Get course topics for self.course, using the given user or self.user if
        not provided, and generating absolute URIs with a test scheme/host.
        """
        return get_course_topics(self.course.id, user or self.user)

    def make_expected_tree(self, topic_id, name, children=None):
        """
        Build an expected result tree given a topic id, display name, and
        children
        """
        children = children or []
        node = {
            "id": topic_id,
            "name": name,
            "children": children,
        }
        return node

    def test_nonexistent_course(self):
        with self.assertRaises(Http404):
            get_course_topics(CourseLocator.from_string("non/existent/course"), self.user)

    def test_not_enrolled(self):
        unenrolled_user = UserFactory.create()
        with self.assertRaises(Http404):
            get_course_topics(self.course.id, unenrolled_user)

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
        self.course.discussion_topics = {
            "A": {"id": "non-courseware-1"},
            "B": {"id": "non-courseware-2"},
        }
        modulestore().update_item(self.course, self.user.id)
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
        self.course.discussion_topics = {
            "W": {"id": "non-courseware-1", "sort_key": "Z"},
            "X": {"id": "non-courseware-2"},
            "Y": {"id": "non-courseware-3", "sort_key": "Y"},
            "Z": {"id": "non-courseware-4", "sort_key": "W"},
        }
        modulestore().update_item(self.course, self.user.id)
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

        beta_actual = self.get_course_topics(beta_tester)
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

        staff_actual = self.get_course_topics(staff)
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
class GetThreadListTest(CommentsServiceMockMixin, ModuleStoreTestCase):
    """Test for get_thread_list"""
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
        self.course = CourseFactory.create()
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.author = UserFactory.create()
        self.cohort = CohortFactory.create(course_id=self.course.id)

    def get_thread_list(self, threads, page=1, page_size=1, num_pages=1, course=None):
        """
        Register the appropriate comments service response, then call
        get_thread_list and return the result.
        """
        course = course or self.course
        self.register_get_threads_response(threads, page, num_pages)
        ret = get_thread_list(self.request, course.id, page, page_size)
        return ret

    def create_role(self, role_name, users):
        """Create a Role in self.course with the given name and users"""
        role = Role.objects.create(name=role_name, course_id=self.course.id)
        role.users = users
        role.save()

    def make_cs_thread(self, thread_data):
        """
        Create a dictionary containing all needed thread fields as returned by
        the comments service with dummy data overridden by thread_data
        """
        ret = {
            "id": "dummy",
            "course_id": unicode(self.course.id),
            "commentable_id": "dummy",
            "group_id": None,
            "user_id": str(self.author.id),
            "username": self.author.username,
            "anonymous": False,
            "anonymous_to_peers": False,
            "created_at": "1970-01-01T00:00:00Z",
            "updated_at": "1970-01-01T00:00:00Z",
            "thread_type": "discussion",
            "title": "dummy",
            "body": "dummy",
            "pinned": False,
            "closed": False,
            "abuse_flaggers": [],
            "votes": {"up_count": 0},
            "comments_count": 0,
            "unread_comments_count": 0,
        }
        ret.update(thread_data)
        return ret

    def test_nonexistent_course(self):
        with self.assertRaises(Http404):
            get_thread_list(self.request, CourseLocator.from_string("non/existent/course"), 1, 1)

    def test_not_enrolled(self):
        self.request.user = UserFactory.create()
        with self.assertRaises(Http404):
            self.get_thread_list([])

    def test_discussions_disabled(self):
        _remove_discussion_tab(self.course, self.user.id)
        with self.assertRaises(Http404):
            self.get_thread_list([])

    def test_empty(self):
        self.assertEqual(
            self.get_thread_list([]),
            {
                "results": [],
                "next": None,
                "previous": None,
            }
        )

    def test_basic_query_params(self):
        self.get_thread_list([], page=6, page_size=14)
        self.assert_last_query_params({
            "course_id": [unicode(self.course.id)],
            "sort_key": ["date"],
            "sort_order": ["desc"],
            "page": ["6"],
            "per_page": ["14"],
            "recursive": ["False"],
        })

    def test_thread_content(self):
        self.register_get_user_response(
            self.user,
            subscribed_thread_ids=["test_thread_id_0"],
            upvoted_ids=["test_thread_id_1"]
        )
        source_threads = [
            {
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
            },
            {
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
                "closed": True,
                "abuse_flaggers": [],
                "votes": {"up_count": 9},
                "comments_count": 18,
                "unread_comments_count": 0,
            },
            {
                "id": "test_thread_id_2",
                "course_id": unicode(self.course.id),
                "commentable_id": "topic_x",
                "group_id": self.cohort.id + 1,  # non-existent group
                "user_id": str(self.author.id),
                "username": self.author.username,
                "anonymous": False,
                "anonymous_to_peers": False,
                "created_at": "2015-04-28T00:44:44Z",
                "updated_at": "2015-04-28T00:55:55Z",
                "thread_type": "discussion",
                "title": "Yet Another Test Title",
                "body": "Still more content",
                "pinned": True,
                "closed": False,
                "abuse_flaggers": [str(self.user.id)],
                "votes": {"up_count": 0},
                "comments_count": 0,
                "unread_comments_count": 0,
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
                "pinned": False,
                "closed": False,
                "following": True,
                "abuse_flagged": False,
                "voted": False,
                "vote_count": 4,
                "comment_count": 5,
                "unread_comment_count": 3,
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
                "pinned": False,
                "closed": True,
                "following": False,
                "abuse_flagged": False,
                "voted": True,
                "vote_count": 9,
                "comment_count": 18,
                "unread_comment_count": 0,
            },
            {
                "id": "test_thread_id_2",
                "course_id": unicode(self.course.id),
                "topic_id": "topic_x",
                "group_id": self.cohort.id + 1,
                "group_name": None,
                "author": self.author.username,
                "author_label": None,
                "created_at": "2015-04-28T00:44:44Z",
                "updated_at": "2015-04-28T00:55:55Z",
                "type": "discussion",
                "title": "Yet Another Test Title",
                "raw_body": "Still more content",
                "pinned": True,
                "closed": False,
                "following": False,
                "abuse_flagged": True,
                "voted": False,
                "vote_count": 0,
                "comment_count": 0,
                "unread_comment_count": 0,
            },
        ]
        self.assertEqual(
            self.get_thread_list(source_threads),
            {
                "results": expected_threads,
                "next": None,
                "previous": None,
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
            }
        )
        self.assertEqual(
            self.get_thread_list([], page=2, num_pages=3),
            {
                "results": [],
                "next": "http://testserver/test_path?page=3",
                "previous": "http://testserver/test_path?page=1",
            }
        )
        self.assertEqual(
            self.get_thread_list([], page=3, num_pages=3),
            {
                "results": [],
                "next": None,
                "previous": "http://testserver/test_path?page=2",
            }
        )

        # Test page past the last one
        self.register_get_threads_response([], page=3, num_pages=3)
        with self.assertRaises(Http404):
            get_thread_list(self.request, self.course.id, page=4, page_size=10)

    @ddt.data(
        (FORUM_ROLE_ADMINISTRATOR, True, False, True),
        (FORUM_ROLE_ADMINISTRATOR, False, True, False),
        (FORUM_ROLE_MODERATOR, True, False, True),
        (FORUM_ROLE_MODERATOR, False, True, False),
        (FORUM_ROLE_COMMUNITY_TA, True, False, True),
        (FORUM_ROLE_COMMUNITY_TA, False, True, False),
        (FORUM_ROLE_STUDENT, True, False, True),
        (FORUM_ROLE_STUDENT, False, True, True),
    )
    @ddt.unpack
    def test_anonymity(self, role_name, anonymous, anonymous_to_peers, expected_api_anonymous):
        """
        Test that a thread is properly made anonymous.

        A thread should be anonymous iff the anonymous field is true or the
        anonymous_to_peers field is true and the requester does not have a
        privileged role.

        role_name is the name of the requester's role.
        thread_anon is the value of the anonymous field in the thread data.
        thread_anon_to_peers is the value of the anonymous_to_peers field in the
          thread data.
        expected_api_anonymous is whether the thread should actually be
          anonymous in the API output when requested by a user with the given
          role.
        """
        self.create_role(role_name, [self.user])
        result = self.get_thread_list([
            self.make_cs_thread({
                "anonymous": anonymous,
                "anonymous_to_peers": anonymous_to_peers,
            })
        ])
        actual_api_anonymous = result["results"][0]["author"] is None
        self.assertEqual(actual_api_anonymous, expected_api_anonymous)

    @ddt.data(
        (FORUM_ROLE_ADMINISTRATOR, False, "staff"),
        (FORUM_ROLE_ADMINISTRATOR, True, None),
        (FORUM_ROLE_MODERATOR, False, "staff"),
        (FORUM_ROLE_MODERATOR, True, None),
        (FORUM_ROLE_COMMUNITY_TA, False, "community_ta"),
        (FORUM_ROLE_COMMUNITY_TA, True, None),
        (FORUM_ROLE_STUDENT, False, None),
        (FORUM_ROLE_STUDENT, True, None),
    )
    @ddt.unpack
    def test_author_labels(self, role_name, anonymous, expected_label):
        """
        Test correctness of the author_label field.

        The label should be "staff", "staff", or "community_ta" for the
        Administrator, Moderator, and Community TA roles, respectively, but
        the label should not be present if the thread is anonymous.

        role_name is the name of the author's role.
        anonymous is the value of the anonymous field in the thread data.
        expected_label is the expected value of the author_label field in the
          API output.
        """
        self.create_role(role_name, [self.author])
        result = self.get_thread_list([self.make_cs_thread({"anonymous": anonymous})])
        actual_label = result["results"][0]["author_label"]
        self.assertEqual(actual_label, expected_label)
