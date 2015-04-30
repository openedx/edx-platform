"""
Tests for Discussion API internal interface
"""
from datetime import datetime, timedelta

import mock
from pytz import UTC

from courseware.tests.factories import BetaTesterFactory, StaffFactory
from discussion_api.api import get_course_topics
from openedx.core.djangoapps.course_groups.models import CourseUserGroupPartitionGroup
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.partitions.partitions import Group, UserPartition


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
            discussion_topics={},
            user_partitions=[self.partition],
            cohort_config={"cohorted": True},
            days_early_for_beta=3
        )
        self.user = UserFactory.create()

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
        return get_course_topics(self.course, user or self.user)

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

    def test_empty(self):
        actual = self.get_course_topics()
        expected = {
            "courseware_topics": [],
            "non_courseware_topics": [],
        }
        self.assertEqual(actual, expected)

    def test_non_courseware(self):
        self.course.discussion_topics = {"Topic Name": {"id": "topic-id"}}
        self.course.save()
        actual = self.get_course_topics()
        expected = {
            "courseware_topics": [],
            "non_courseware_topics": [self.make_expected_tree("topic-id", "Topic Name")],
        }
        self.assertEqual(actual, expected)

    def test_courseware(self):
        self.make_discussion_module("topic-id", "Foo", "Bar")
        actual = self.get_course_topics()
        expected = {
            "courseware_topics": [
                self.make_expected_tree(
                    None,
                    "Foo",
                    [self.make_expected_tree("topic-id", "Bar")]
                ),
            ],
            "non_courseware_topics": [],
        }
        self.assertEqual(actual, expected)

    def test_many(self):
        self.make_discussion_module("courseware-1", "A", "1")
        self.make_discussion_module("courseware-2", "A", "2")
        self.make_discussion_module("courseware-3", "B", "1")
        self.make_discussion_module("courseware-4", "B", "2")
        self.make_discussion_module("courseware-5", "C", "1")
        self.course.discussion_topics = {
            "A": {"id": "non-courseware-1"},
            "B": {"id": "non-courseware-2"},
        }
        self.course.save()
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
        self.make_discussion_module("courseware-1", "First", "A", sort_key="D")
        self.make_discussion_module("courseware-2", "First", "B", sort_key="B")
        self.make_discussion_module("courseware-3", "First", "C", sort_key="E")
        self.make_discussion_module("courseware-4", "Second", "A", sort_key="F")
        self.make_discussion_module("courseware-5", "Second", "B", sort_key="G")
        self.make_discussion_module("courseware-6", "Second", "C")
        self.make_discussion_module("courseware-7", "Second", "D", sort_key="A")
        self.course.discussion_topics = {
            "W": {"id": "non-courseware-1", "sort_key": "Z"},
            "X": {"id": "non-courseware-2"},
            "Y": {"id": "non-courseware-3", "sort_key": "Y"},
            "Z": {"id": "non-courseware-4", "sort_key": "W"},
        }
        self.course.save()
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
            "non_courseware_topics": [],
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
            "non_courseware_topics": [],
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
            "non_courseware_topics": [],
        }
        self.assertEqual(staff_actual, staff_expected)
