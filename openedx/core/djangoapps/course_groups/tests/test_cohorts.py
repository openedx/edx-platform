"""
Tests for cohorts
"""
# pylint: disable=no-member
import ddt
from mock import call, patch
from nose.plugins.attrib import attr
import before_after

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import Http404
from django.test import TestCase

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import TEST_DATA_MIXED_MODULESTORE, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory

from ..models import CourseUserGroup, CourseCohort, CourseUserGroupPartitionGroup
from .. import cohorts
from ..tests.helpers import (
    topic_name_to_id, config_course_cohorts, config_course_cohorts_legacy,
    CohortFactory, CourseCohortFactory, CourseCohortSettingsFactory
)


@attr('shard_2')
@patch("openedx.core.djangoapps.course_groups.cohorts.tracker", autospec=True)
class TestCohortSignals(TestCase):
    """
    Test cases to validate event emissions for various cohort-related workflows
    """

    def setUp(self):
        super(TestCohortSignals, self).setUp()
        self.course_key = SlashSeparatedCourseKey("dummy", "dummy", "dummy")

    def test_cohort_added(self, mock_tracker):
        # Add cohort
        cohort = CourseUserGroup.objects.create(
            name="TestCohort",
            course_id=self.course_key,
            group_type=CourseUserGroup.COHORT
        )
        mock_tracker.emit.assert_called_with(
            "edx.cohort.created",
            {"cohort_id": cohort.id, "cohort_name": cohort.name}
        )
        mock_tracker.reset_mock()

        # Modify existing cohort
        cohort.name = "NewName"
        cohort.save()
        self.assertFalse(mock_tracker.called)

        # Add non-cohort group
        CourseUserGroup.objects.create(
            name="TestOtherGroupType",
            course_id=self.course_key,
            group_type="dummy"
        )
        self.assertFalse(mock_tracker.called)

    def test_cohort_membership_changed(self, mock_tracker):
        cohort_list = [CohortFactory() for _ in range(2)]
        non_cohort = CourseUserGroup.objects.create(
            name="dummy",
            course_id=self.course_key,
            group_type="dummy"
        )
        user_list = [UserFactory() for _ in range(2)]
        mock_tracker.reset_mock()

        def assert_events(event_name_suffix, user_list, cohort_list):
            """
            Confirms the presence of the specifed event for each user in the specified list of cohorts
            """
            mock_tracker.emit.assert_has_calls([
                call(
                    "edx.cohort.user_" + event_name_suffix,
                    {
                        "user_id": user.id,
                        "cohort_id": cohort.id,
                        "cohort_name": cohort.name,
                    }
                )
                for user in user_list for cohort in cohort_list
            ])

        # Add users to cohort
        cohort_list[0].users.add(*user_list)
        assert_events("added", user_list, cohort_list[:1])
        mock_tracker.reset_mock()

        # Remove users from cohort
        cohort_list[0].users.remove(*user_list)
        assert_events("removed", user_list, cohort_list[:1])
        mock_tracker.reset_mock()

        # Clear users from cohort
        cohort_list[0].users.add(*user_list)
        cohort_list[0].users.clear()
        assert_events("removed", user_list, cohort_list[:1])
        mock_tracker.reset_mock()

        # Clear users from non-cohort group
        non_cohort.users.add(*user_list)
        non_cohort.users.clear()
        self.assertFalse(mock_tracker.emit.called)

        # Add cohorts to user
        user_list[0].course_groups.add(*cohort_list)
        assert_events("added", user_list[:1], cohort_list)
        mock_tracker.reset_mock()

        # Remove cohorts from user
        user_list[0].course_groups.remove(*cohort_list)
        assert_events("removed", user_list[:1], cohort_list)
        mock_tracker.reset_mock()

        # Clear cohorts from user
        user_list[0].course_groups.add(*cohort_list)
        user_list[0].course_groups.clear()
        assert_events("removed", user_list[:1], cohort_list)
        mock_tracker.reset_mock()

        # Clear non-cohort groups from user
        user_list[0].course_groups.add(non_cohort)
        user_list[0].course_groups.clear()
        self.assertFalse(mock_tracker.emit.called)


@attr('shard_2')
@ddt.ddt
class TestCohorts(ModuleStoreTestCase):
    """
    Test the cohorts feature
    """
    MODULESTORE = TEST_DATA_MIXED_MODULESTORE

    def setUp(self):
        """
        Make sure that course is reloaded every time--clear out the modulestore.
        """
        super(TestCohorts, self).setUp()
        self.toy_course_key = ToyCourseFactory.create().id

    def _create_cohort(self, course_id, cohort_name, assignment_type):
        """
        Create a cohort for testing.
        """
        cohort = CohortFactory(course_id=course_id, name=cohort_name)
        CourseCohortFactory(course_user_group=cohort, assignment_type=assignment_type)
        return cohort

    def test_is_course_cohorted(self):
        """
        Make sure cohorts.is_course_cohorted() correctly reports if a course is cohorted or not.
        """
        course = modulestore().get_course(self.toy_course_key)
        self.assertFalse(cohorts.is_course_cohorted(course.id))

        config_course_cohorts(course, is_cohorted=True)

        self.assertTrue(cohorts.is_course_cohorted(course.id))

        # Make sure we get a Http404 if there's no course
        fake_key = SlashSeparatedCourseKey('a', 'b', 'c')
        self.assertRaises(Http404, lambda: cohorts.is_course_cohorted(fake_key))

    def test_get_cohort_id(self):
        """
        Make sure that cohorts.get_cohort_id() correctly returns the cohort id, or raises a ValueError when given an
        invalid course key.
        """
        course = modulestore().get_course(self.toy_course_key)
        self.assertFalse(cohorts.is_course_cohorted(course.id))

        user = UserFactory(username="test", email="a@b.com")
        self.assertIsNone(cohorts.get_cohort_id(user, course.id))

        config_course_cohorts(course, is_cohorted=True)
        cohort = CohortFactory(course_id=course.id, name="TestCohort", users=[user])
        self.assertEqual(cohorts.get_cohort_id(user, course.id), cohort.id)

        self.assertRaises(
            Http404,
            lambda: cohorts.get_cohort_id(user, SlashSeparatedCourseKey("course", "does_not", "exist"))
        )

    def test_assignment_type(self):
        """
        Make sure that cohorts.set_assignment_type() and cohorts.get_assignment_type() works correctly.
        """
        course = modulestore().get_course(self.toy_course_key)

        # We are creating two random cohorts because we can't change assignment type of
        # random cohort if it is the only random cohort present.
        cohort1 = self._create_cohort(course.id, "TestCohort1", CourseCohort.RANDOM)
        self._create_cohort(course.id, "TestCohort2", CourseCohort.RANDOM)
        cohort3 = self._create_cohort(course.id, "TestCohort3", CourseCohort.MANUAL)

        self.assertEqual(cohorts.get_assignment_type(cohort1), CourseCohort.RANDOM)

        cohorts.set_assignment_type(cohort1, CourseCohort.MANUAL)
        self.assertEqual(cohorts.get_assignment_type(cohort1), CourseCohort.MANUAL)

        cohorts.set_assignment_type(cohort3, CourseCohort.RANDOM)
        self.assertEqual(cohorts.get_assignment_type(cohort3), CourseCohort.RANDOM)

    def test_cannot_set_assignment_type(self):
        """
        Make sure that we can't change the assignment type of a random cohort if it is the only random cohort present.
        """
        course = modulestore().get_course(self.toy_course_key)

        cohort = self._create_cohort(course.id, "TestCohort", CourseCohort.RANDOM)

        self.assertEqual(cohorts.get_assignment_type(cohort), CourseCohort.RANDOM)

        exception_msg = "There must be one cohort to which students can automatically be assigned."
        with self.assertRaises(ValueError) as context_manager:
            cohorts.set_assignment_type(cohort, CourseCohort.MANUAL)

        self.assertEqual(exception_msg, str(context_manager.exception))

    def test_get_cohort(self):
        """
        Make sure cohorts.get_cohort() does the right thing when the course is cohorted
        """
        course = modulestore().get_course(self.toy_course_key)
        self.assertEqual(course.id, self.toy_course_key)
        self.assertFalse(cohorts.is_course_cohorted(course.id))

        user = UserFactory(username="test", email="a@b.com")
        other_user = UserFactory(username="test2", email="a2@b.com")

        self.assertIsNone(cohorts.get_cohort(user, course.id), "No cohort created yet")

        cohort = CohortFactory(course_id=course.id, name="TestCohort", users=[user])

        self.assertIsNone(
            cohorts.get_cohort(user, course.id),
            "Course isn't cohorted, so shouldn't have a cohort"
        )

        # Make the course cohorted...
        config_course_cohorts(course, is_cohorted=True)

        self.assertEquals(
            cohorts.get_cohort(user, course.id).id,
            cohort.id,
            "user should be assigned to the correct cohort"
        )

        self.assertEquals(
            cohorts.get_cohort(other_user, course.id).id,
            cohorts.get_cohort_by_name(course.id, cohorts.DEFAULT_COHORT_NAME).id,
            "other_user should be assigned to the default cohort"
        )

    @ddt.data(
        (True, 3),
        (False, 9),
    )
    @ddt.unpack
    def test_get_cohort_sql_queries(self, use_cached, num_sql_queries):
        """
        Test number of queries by cohorts.get_cohort() with and without caching.
        """
        course = modulestore().get_course(self.toy_course_key)
        config_course_cohorts(course, is_cohorted=True)
        user = UserFactory(username="test", email="a@b.com")
        CohortFactory.create(course_id=course.id, name="TestCohort", users=[user])

        with self.assertNumQueries(num_sql_queries):
            for __ in range(3):
                cohorts.get_cohort(user, course.id, use_cached=use_cached)

    def test_get_cohort_with_assign(self):
        """
        Make sure cohorts.get_cohort() returns None if no group is already
        assigned to a user instead of assigning/creating a group automatically
        """
        course = modulestore().get_course(self.toy_course_key)
        self.assertFalse(cohorts.is_course_cohorted(course.id))

        user = UserFactory(username="test", email="a@b.com")

        # Add an auto_cohort_group to the course...
        config_course_cohorts(
            course,
            is_cohorted=True,
            auto_cohorts=["AutoGroup"]
        )

        # get_cohort should return None as no group is assigned to user
        self.assertIsNone(cohorts.get_cohort(user, course.id, assign=False))

        # get_cohort should return a group for user
        self.assertEquals(cohorts.get_cohort(user, course.id).name, "AutoGroup")

    def test_cohorting_with_auto_cohorts(self):
        """
        Make sure cohorts.get_cohort() does the right thing.
        If there are auto cohort groups then a user should be assigned one.
        """
        course = modulestore().get_course(self.toy_course_key)
        self.assertFalse(cohorts.is_course_cohorted(course.id))

        user1 = UserFactory(username="test", email="a@b.com")
        user2 = UserFactory(username="test2", email="a2@b.com")

        cohort = CohortFactory(course_id=course.id, name="TestCohort", users=[user1])

        # Add an auto_cohort_group to the course...
        config_course_cohorts(
            course,
            is_cohorted=True,
            auto_cohorts=["AutoGroup"]
        )

        self.assertEquals(cohorts.get_cohort(user1, course.id).id, cohort.id, "user1 should stay put")

        self.assertEquals(cohorts.get_cohort(user2, course.id).name, "AutoGroup", "user2 should be auto-cohorted")

    def test_cohorting_with_migrations_done(self):
        """
        Verifies that cohort config changes on studio/moduletore side will
        not be reflected on lms after the migrations are done.
        """
        course = modulestore().get_course(self.toy_course_key)

        user1 = UserFactory(username="test", email="a@b.com")
        user2 = UserFactory(username="test2", email="a2@b.com")

        # Add an auto_cohort_group to the course...
        config_course_cohorts(
            course,
            is_cohorted=True,
            auto_cohorts=["AutoGroup"]
        )

        self.assertEquals(cohorts.get_cohort(user1, course.id).name, "AutoGroup", "user1 should be auto-cohorted")

        # Now set the auto_cohort_group to something different
        # This will have no effect on lms side as we are already done with migrations
        config_course_cohorts_legacy(
            course,
            discussions=[],
            cohorted=True,
            auto_cohort_groups=["OtherGroup"]
        )

        self.assertEquals(
            cohorts.get_cohort(user2, course.id).name, "AutoGroup", "user2 should be assigned to AutoGroups"
        )

        self.assertEquals(
            cohorts.get_cohort(user1, course.id).name, "AutoGroup", "user1 should still be in originally placed cohort"
        )

    def test_cohorting_with_no_auto_cohorts(self):
        """
        Make sure cohorts.get_cohort() does the right thing.
        If there are not auto cohorts then a user should be assigned to Default Cohort Group.
        Also verifies that cohort config changes on studio/moduletore side will
        not be reflected on lms after the migrations are done.
        """
        course = modulestore().get_course(self.toy_course_key)
        self.assertFalse(cohorts.is_course_cohorted(course.id))

        user1 = UserFactory(username="test", email="a@b.com")
        user2 = UserFactory(username="test2", email="a2@b.com")

        # Make the auto_cohort_group list empty
        config_course_cohorts(
            course,
            is_cohorted=True,
            auto_cohorts=[]
        )

        self.assertEquals(
            cohorts.get_cohort(user1, course.id).id,
            cohorts.get_cohort_by_name(course.id, cohorts.DEFAULT_COHORT_NAME).id,
            "No groups->default cohort for user1"
        )

        # Add an auto_cohort_group to the course
        # This will have no effect on lms side as we are already done with migrations
        config_course_cohorts_legacy(
            course,
            discussions=[],
            cohorted=True,
            auto_cohort_groups=["AutoGroup"]
        )

        self.assertEquals(
            cohorts.get_cohort(user1, course.id).name,
            cohorts.get_cohort_by_name(course.id, cohorts.DEFAULT_COHORT_NAME).name,
            "user1 should still be in the default cohort"
        )

        self.assertEquals(
            cohorts.get_cohort(user2, course.id).id,
            cohorts.get_cohort_by_name(course.id, cohorts.DEFAULT_COHORT_NAME).id,
            "No groups->default cohort for user2"
        )

    def test_auto_cohorting_randomization(self):
        """
        Make sure cohorts.get_cohort() randomizes properly.
        """
        course = modulestore().get_course(self.toy_course_key)
        self.assertFalse(cohorts.is_course_cohorted(course.id))

        groups = ["group_{0}".format(n) for n in range(5)]
        config_course_cohorts(
            course, is_cohorted=True, auto_cohorts=groups
        )

        # Assign 100 users to cohorts
        for i in range(100):
            user = UserFactory(
                username="test_{0}".format(i),
                email="a@b{0}.com".format(i)
            )
            cohorts.get_cohort(user, course.id)

        # Now make sure that the assignment was at least vaguely random:
        # each cohort should have at least 1, and fewer than 50 students.
        # (with 5 groups, probability of 0 users in any group is about
        # .8**100= 2.0e-10)
        for cohort_name in groups:
            cohort = cohorts.get_cohort_by_name(course.id, cohort_name)
            num_users = cohort.users.count()
            self.assertGreater(num_users, 1)
            self.assertLess(num_users, 50)

    def test_get_course_cohorts_noop(self):
        """
        Tests get_course_cohorts returns an empty list when no cohorts exist.
        """
        course = modulestore().get_course(self.toy_course_key)
        config_course_cohorts(course, is_cohorted=True)
        self.assertEqual([], cohorts.get_course_cohorts(course))

    def test_get_course_cohorts(self):
        """
        Tests that get_course_cohorts returns all cohorts, including auto cohorts.
        """
        course = modulestore().get_course(self.toy_course_key)
        config_course_cohorts(
            course,
            is_cohorted=True,
            auto_cohorts=["AutoGroup1", "AutoGroup2"]
        )

        # add manual cohorts to course 1
        CohortFactory(course_id=course.id, name="ManualCohort")
        CohortFactory(course_id=course.id, name="ManualCohort2")

        cohort_set = {c.name for c in cohorts.get_course_cohorts(course)}
        self.assertEqual(cohort_set, {"AutoGroup1", "AutoGroup2", "ManualCohort", "ManualCohort2"})

    def test_get_cohort_names(self):
        course = modulestore().get_course(self.toy_course_key)
        cohort1 = CohortFactory(course_id=course.id, name="Cohort1")
        cohort2 = CohortFactory(course_id=course.id, name="Cohort2")
        self.assertEqual(
            cohorts.get_cohort_names(course),
            {cohort1.id: cohort1.name, cohort2.id: cohort2.name}
        )

    def test_get_cohorted_commentables(self):
        """
        Make sure cohorts.get_cohorted_commentables() correctly returns a list of strings representing cohorted
        commentables.  Also verify that we can't get the cohorted commentables from a course which does not exist.
        """
        course = modulestore().get_course(self.toy_course_key)

        self.assertEqual(cohorts.get_cohorted_commentables(course.id), set())

        config_course_cohorts(course, is_cohorted=True)
        self.assertEqual(cohorts.get_cohorted_commentables(course.id), set())

        config_course_cohorts(
            course,
            is_cohorted=True,
            discussion_topics=["General", "Feedback"],
            cohorted_discussions=["Feedback"]
        )
        self.assertItemsEqual(
            cohorts.get_cohorted_commentables(course.id),
            set([topic_name_to_id(course, "Feedback")])
        )

        config_course_cohorts(
            course,
            is_cohorted=True,
            discussion_topics=["General", "Feedback"],
            cohorted_discussions=["General", "Feedback"]
        )
        self.assertItemsEqual(
            cohorts.get_cohorted_commentables(course.id),
            set([topic_name_to_id(course, "General"), topic_name_to_id(course, "Feedback")])
        )
        self.assertRaises(
            Http404,
            lambda: cohorts.get_cohorted_commentables(SlashSeparatedCourseKey("course", "does_not", "exist"))
        )

    def test_get_cohort_by_name(self):
        """
        Make sure cohorts.get_cohort_by_name() properly finds a cohort by name for a given course.  Also verify that it
        raises an error when the cohort is not found.
        """
        course = modulestore().get_course(self.toy_course_key)

        self.assertRaises(
            CourseUserGroup.DoesNotExist,
            lambda: cohorts.get_cohort_by_name(course.id, "CohortDoesNotExist")
        )

        cohort = CohortFactory(course_id=course.id, name="MyCohort")

        self.assertEqual(cohorts.get_cohort_by_name(course.id, "MyCohort"), cohort)

        self.assertRaises(
            CourseUserGroup.DoesNotExist,
            lambda: cohorts.get_cohort_by_name(SlashSeparatedCourseKey("course", "does_not", "exist"), cohort)
        )

    def test_get_cohort_by_id(self):
        """
        Make sure cohorts.get_cohort_by_id() properly finds a cohort by id for a given
        course.
        """
        course = modulestore().get_course(self.toy_course_key)
        cohort = CohortFactory(course_id=course.id, name="MyCohort")

        self.assertEqual(cohorts.get_cohort_by_id(course.id, cohort.id), cohort)

        cohort.delete()

        self.assertRaises(
            CourseUserGroup.DoesNotExist,
            lambda: cohorts.get_cohort_by_id(course.id, cohort.id)
        )

    @patch("openedx.core.djangoapps.course_groups.cohorts.tracker")
    def test_add_cohort(self, mock_tracker):
        """
        Make sure cohorts.add_cohort() properly adds a cohort to a course and handles
        errors.
        """
        assignment_type = CourseCohort.RANDOM
        course = modulestore().get_course(self.toy_course_key)
        added_cohort = cohorts.add_cohort(course.id, "My Cohort", assignment_type)
        mock_tracker.emit.assert_any_call(
            "edx.cohort.creation_requested",
            {"cohort_name": added_cohort.name, "cohort_id": added_cohort.id}
        )

        self.assertEqual(added_cohort.name, "My Cohort")
        self.assertRaises(
            ValueError,
            lambda: cohorts.add_cohort(course.id, "My Cohort", assignment_type)
        )
        does_not_exist_course_key = SlashSeparatedCourseKey("course", "does_not", "exist")
        self.assertRaises(
            ValueError,
            lambda: cohorts.add_cohort(does_not_exist_course_key, "My Cohort", assignment_type)
        )

    @patch("openedx.core.djangoapps.course_groups.cohorts.tracker")
    def test_add_user_to_cohort(self, mock_tracker):
        """
        Make sure cohorts.add_user_to_cohort() properly adds a user to a cohort and
        handles errors.
        """
        course_user = UserFactory(username="Username", email="a@b.com")
        UserFactory(username="RandomUsername", email="b@b.com")
        course = modulestore().get_course(self.toy_course_key)
        CourseEnrollment.enroll(course_user, self.toy_course_key)
        first_cohort = CohortFactory(course_id=course.id, name="FirstCohort")
        second_cohort = CohortFactory(course_id=course.id, name="SecondCohort")

        # Success cases
        # We shouldn't get back a previous cohort, since the user wasn't in one
        self.assertEqual(
            cohorts.add_user_to_cohort(first_cohort, "Username"),
            (course_user, None)
        )
        mock_tracker.emit.assert_any_call(
            "edx.cohort.user_add_requested",
            {
                "user_id": course_user.id,
                "cohort_id": first_cohort.id,
                "cohort_name": first_cohort.name,
                "previous_cohort_id": None,
                "previous_cohort_name": None,
            }
        )
        # Should get (user, previous_cohort_name) when moved from one cohort to
        # another
        self.assertEqual(
            cohorts.add_user_to_cohort(second_cohort, "Username"),
            (course_user, "FirstCohort")
        )
        mock_tracker.emit.assert_any_call(
            "edx.cohort.user_add_requested",
            {
                "user_id": course_user.id,
                "cohort_id": second_cohort.id,
                "cohort_name": second_cohort.name,
                "previous_cohort_id": first_cohort.id,
                "previous_cohort_name": first_cohort.name,
            }
        )
        # Error cases
        # Should get AlreadyAddedToCohortException if user already in cohort
        self.assertRaises(
            ValueError,
            lambda: cohorts.add_user_to_cohort(second_cohort, "Username")
        )
        # UserDoesNotExist if user truly does not exist
        self.assertRaises(
            User.DoesNotExist,
            lambda: cohorts.add_user_to_cohort(first_cohort, "non_existent_username")
        )

    @patch("openedx.core.djangoapps.course_groups.cohorts.tracker")
    def add_user_to_cohorts_race_condition(self, mock_tracker):
        """
        Makes use of before_after to force a race condition, in order to
        confirm handling of such conditions is done correctly.
        """
        course_user = UserFactory(username="Username", email="a@b.com")
        course = modulestore().get_course(self.toy_course_key)
        CourseEnrollment.enroll(course_user, self.toy_course_key)
        first_cohort = CohortFactory(course_id=course.id, name="FirstCohort")
        second_cohort = CohortFactory(course_id=course.id, name="SecondCohort")

        # This before_after contextmanager allows for reliable reproduction of a race condition.
        # It will break before the first save() call creates an entry, and then run add_user_to_cohort again.
        # Because this second call will write before control is returned, the first call will be writing stale data.
        # This test confirms that the first add_user_to_cohort call can handle this stale read condition properly.
        # Proper handling is defined as treating calls as sequential, with write time deciding the order.
        with before_after.before_after(
            'django.db.models.Model.save',
            after_ftn=cohorts.add_user_to_cohort(second_cohort, course_user.username),
            autospec=True
        ):
            # This method will read, then break, then try to write stale data.
            # It should fail at that, then retry with refreshed data
            cohorts.add_user_to_cohort(first_cohort, course_user.username)

        mock_tracker.emit.assert_any_call(
            "edx.cohort.user_add_requested",
            {
                "user_id": course_user.id,
                "cohort_id": first_cohort.id,
                "cohort_name": first_cohort.name,
                "previous_cohort_id": second_cohort.id,
                "previous_cohort_name": second_cohort.name,
            }
        )
        # Note that the following get() will fail with MultipleObjectsReturned if race condition is not handled.
        self.assertEqual(first_cohort.users.get(), course_user)

    def test_get_course_cohort_settings(self):
        """
        Test that cohorts.get_course_cohort_settings is working as expected.
        """
        course = modulestore().get_course(self.toy_course_key)
        course_cohort_settings = cohorts.get_course_cohort_settings(course.id)

        self.assertFalse(course_cohort_settings.is_cohorted)
        self.assertEqual(course_cohort_settings.cohorted_discussions, [])
        self.assertTrue(course_cohort_settings.always_cohort_inline_discussions)

    def test_update_course_cohort_settings(self):
        """
        Test that cohorts.set_course_cohort_settings is working as expected.
        """
        course = modulestore().get_course(self.toy_course_key)
        CourseCohortSettingsFactory(course_id=course.id)

        cohorts.set_course_cohort_settings(
            course.id,
            is_cohorted=False,
            cohorted_discussions=['topic a id', 'topic b id'],
            always_cohort_inline_discussions=False
        )

        course_cohort_settings = cohorts.get_course_cohort_settings(course.id)

        self.assertFalse(course_cohort_settings.is_cohorted)
        self.assertEqual(course_cohort_settings.cohorted_discussions, ['topic a id', 'topic b id'])
        self.assertFalse(course_cohort_settings.always_cohort_inline_discussions)

    def test_update_course_cohort_settings_with_invalid_data_type(self):
        """
        Test that cohorts.set_course_cohort_settings raises exception if fields have incorrect data type.
        """
        course = modulestore().get_course(self.toy_course_key)
        CourseCohortSettingsFactory(course_id=course.id)

        exception_msg_tpl = "Incorrect field type for `{}`. Type must be `{}`"
        fields = [
            {'name': 'is_cohorted', 'type': bool},
            {'name': 'always_cohort_inline_discussions', 'type': bool},
            {'name': 'cohorted_discussions', 'type': list}
        ]

        for field in fields:
            with self.assertRaises(ValueError) as value_error:
                cohorts.set_course_cohort_settings(course.id, **{field['name']: ''})

            self.assertEqual(
                value_error.exception.message,
                exception_msg_tpl.format(field['name'], field['type'].__name__)
            )


@attr('shard_2')
@ddt.ddt
class TestCohortsAndPartitionGroups(ModuleStoreTestCase):
    """
    Test Cohorts and Partitions Groups.
    """
    MODULESTORE = TEST_DATA_MIXED_MODULESTORE

    def setUp(self):
        """
        Regenerate a test course and cohorts for each test
        """
        super(TestCohortsAndPartitionGroups, self).setUp()

        self.test_course_key = ToyCourseFactory.create().id
        self.course = modulestore().get_course(self.test_course_key)

        self.first_cohort = CohortFactory(course_id=self.course.id, name="FirstCohort")
        self.second_cohort = CohortFactory(course_id=self.course.id, name="SecondCohort")

        self.partition_id = 1
        self.group1_id = 10
        self.group2_id = 20

    def _link_cohort_partition_group(self, cohort, partition_id, group_id):
        """
        Utility to create cohort -> partition group assignments in the database.
        """
        link = CourseUserGroupPartitionGroup(
            course_user_group=cohort,
            partition_id=partition_id,
            group_id=group_id,
        )
        link.save()
        return link

    def test_get_group_info_for_cohort(self):
        """
        Basic test of the partition_group_info accessor function
        """
        # api should return nothing for an unmapped cohort
        self.assertEqual(
            cohorts.get_group_info_for_cohort(self.first_cohort),
            (None, None),
        )
        # create a link for the cohort in the db
        link = self._link_cohort_partition_group(
            self.first_cohort,
            self.partition_id,
            self.group1_id
        )
        # api should return the specified partition and group
        self.assertEqual(
            cohorts.get_group_info_for_cohort(self.first_cohort),
            (self.group1_id, self.partition_id)
        )
        # delete the link in the db
        link.delete()
        # api should return nothing again
        self.assertEqual(
            cohorts.get_group_info_for_cohort(self.first_cohort),
            (None, None),
        )

    @ddt.data(
        (True, 1),
        (False, 3),
    )
    @ddt.unpack
    def test_get_group_info_for_cohort_queries(self, use_cached, num_sql_queries):
        """
        Basic test of the partition_group_info accessor function
        """
        # create a link for the cohort in the db
        self._link_cohort_partition_group(
            self.first_cohort,
            self.partition_id,
            self.group1_id
        )
        with self.assertNumQueries(num_sql_queries):
            for __ in range(3):
                self.assertIsNotNone(cohorts.get_group_info_for_cohort(self.first_cohort, use_cached=use_cached))

    def test_multiple_cohorts(self):
        """
        Test that multiple cohorts can be linked to the same partition group
        """
        self._link_cohort_partition_group(
            self.first_cohort,
            self.partition_id,
            self.group1_id,
        )
        self._link_cohort_partition_group(
            self.second_cohort,
            self.partition_id,
            self.group1_id,
        )
        self.assertEqual(
            cohorts.get_group_info_for_cohort(self.first_cohort),
            (self.group1_id, self.partition_id),
        )
        self.assertEqual(
            cohorts.get_group_info_for_cohort(self.second_cohort),
            cohorts.get_group_info_for_cohort(self.first_cohort),
        )

    def test_multiple_partition_groups(self):
        """
        Test that a cohort cannot be mapped to more than one partition group
        """
        self._link_cohort_partition_group(
            self.first_cohort,
            self.partition_id,
            self.group1_id,
        )
        with self.assertRaises(IntegrityError):
            self._link_cohort_partition_group(
                self.first_cohort,
                self.partition_id,
                self.group2_id,
            )

    def test_delete_cascade(self):
        """
        Test that cohort -> partition group links are automatically deleted
        when their parent cohort is deleted.
        """
        self._link_cohort_partition_group(
            self.first_cohort,
            self.partition_id,
            self.group1_id
        )
        self.assertEqual(
            cohorts.get_group_info_for_cohort(self.first_cohort),
            (self.group1_id, self.partition_id)
        )
        # delete the link
        self.first_cohort.delete()
        # api should return nothing at that point
        self.assertEqual(
            cohorts.get_group_info_for_cohort(self.first_cohort),
            (None, None),
        )
        # link should no longer exist because of delete cascade
        with self.assertRaises(CourseUserGroupPartitionGroup.DoesNotExist):
            CourseUserGroupPartitionGroup.objects.get(
                course_user_group_id=self.first_cohort.id
            )
