"""
Tests for cleanup of users which are added in multiple cohorts of a course
"""
from django.core.exceptions import MultipleObjectsReturned
from django.core.management import call_command
from django.test.client import RequestFactory

from openedx.core.djangoapps.course_groups.views import cohort_handler
from openedx.core.djangoapps.course_groups.cohorts import get_cohort, get_cohort_by_name
from openedx.core.djangoapps.course_groups.tests.helpers import config_course_cohorts
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestMultipleCohortUsers(ModuleStoreTestCase):
    """
    Base class for testing users with multiple cohorts
    """
    def setUp(self):
        """
        setup course, user and request for tests
        """
        super(TestMultipleCohortUsers, self).setUp()
        self.course1 = CourseFactory.create()
        self.course2 = CourseFactory.create()
        self.user1 = UserFactory(is_staff=True)
        self.user2 = UserFactory(is_staff=True)
        self.request = RequestFactory().get("dummy_url")
        self.request.user = self.user1

    def test_users_with_multiple_cohorts_cleanup(self):
        """
        Test that user which have been added in multiple cohorts of a course,
        can get cohorts without error after running cohorts cleanup command
        """
        # set two auto_cohort_groups for both courses
        config_course_cohorts(
            self.course1, is_cohorted=True, auto_cohorts=["Course1AutoGroup1", "Course1AutoGroup2"]
        )
        config_course_cohorts(
            self.course2, is_cohorted=True, auto_cohorts=["Course2AutoGroup1", "Course2AutoGroup2"]
        )

        # get the cohorts from the courses, which will cause auto cohorts to be created
        cohort_handler(self.request, unicode(self.course1.id))
        cohort_handler(self.request, unicode(self.course2.id))
        course_1_auto_cohort_1 = get_cohort_by_name(self.course1.id, "Course1AutoGroup1")
        course_1_auto_cohort_2 = get_cohort_by_name(self.course1.id, "Course1AutoGroup2")
        course_2_auto_cohort_1 = get_cohort_by_name(self.course2.id, "Course2AutoGroup1")

        # forcefully add user1 in two auto cohorts
        course_1_auto_cohort_1.users.add(self.user1)
        course_1_auto_cohort_2.users.add(self.user1)
        # forcefully add user2 in auto cohorts of both courses
        course_1_auto_cohort_1.users.add(self.user2)
        course_2_auto_cohort_1.users.add(self.user2)

        # now check that when user1 goes on discussion page and tries to get
        # cohorts 'MultipleObjectsReturned' exception is returned
        with self.assertRaises(MultipleObjectsReturned):
            get_cohort(self.user1, self.course1.id)
        # also check that user 2 can go on discussion page of both courses
        # without any exception
        get_cohort(self.user2, self.course1.id)
        get_cohort(self.user2, self.course2.id)

        # call command to remove users added in multiple cohorts of a course
        # are removed from all cohort groups
        call_command('remove_users_from_multiple_cohorts')

        # check that only user1 (with multiple cohorts) is removed from cohorts
        # and user2 is still in auto cohorts of both course after running
        # 'remove_users_from_multiple_cohorts' management command
        self.assertEqual(self.user1.course_groups.count(), 0)
        self.assertEqual(self.user2.course_groups.count(), 2)
        user2_cohorts = list(self.user2.course_groups.values_list('name', flat=True))
        self.assertEqual(user2_cohorts, ['Course1AutoGroup1', 'Course2AutoGroup1'])

        # now check that user1 can get cohorts in which he is added
        response = cohort_handler(self.request, unicode(self.course1.id))
        self.assertEqual(response.status_code, 200)
