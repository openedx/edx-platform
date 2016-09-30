"""
Test for the post-migration fix commands that are included with this djangoapp
"""
from django.core.management import call_command
from django.test.client import RequestFactory

from openedx.core.djangoapps.course_groups.views import cohort_handler
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_by_name
from openedx.core.djangoapps.course_groups.tests.helpers import config_course_cohorts
from openedx.core.djangoapps.course_groups.models import CohortMembership
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestPostMigrationFix(ModuleStoreTestCase):
    """
    Base class for testing post-migration fix commands
    """
    def setUp(self):
        """
        setup course, user and request for tests
        """
        super(TestPostMigrationFix, self).setUp()
        self.course1 = CourseFactory.create()
        self.course2 = CourseFactory.create()
        self.user1 = UserFactory(is_staff=True)
        self.user2 = UserFactory(is_staff=True)
        self.request = RequestFactory().get("dummy_url")
        self.request.user = self.user1

    def test_post_cohortmembership_fix(self):
        """
        Test that changes made *after* migration, but *before* turning on new code are handled properly
        """
        # First, we're going to simulate some problem states that can arise during this window
        config_course_cohorts(self.course1, is_cohorted=True, auto_cohorts=["Course1AutoGroup1", "Course1AutoGroup2"])

        # Get the cohorts from the courses, which will cause auto cohorts to be created
        cohort_handler(self.request, unicode(self.course1.id))
        course_1_auto_cohort_1 = get_cohort_by_name(self.course1.id, "Course1AutoGroup1")
        course_1_auto_cohort_2 = get_cohort_by_name(self.course1.id, "Course1AutoGroup2")

        # When migrations were first run, the users were assigned to CohortMemberships correctly
        membership1 = CohortMembership(
            course_id=course_1_auto_cohort_1.course_id,
            user=self.user1,
            course_user_group=course_1_auto_cohort_1
        )
        membership1.save()
        membership2 = CohortMembership(
            course_id=course_1_auto_cohort_1.course_id,
            user=self.user2,
            course_user_group=course_1_auto_cohort_1
        )
        membership2.save()

        # But before CohortMembership code was turned on, some changes were made:
        course_1_auto_cohort_2.users.add(self.user1)  # user1 is now in 2 cohorts in the same course!
        course_1_auto_cohort_2.users.add(self.user2)
        course_1_auto_cohort_1.users.remove(self.user2)  # and user2 was moved, but no one told CohortMembership!

        # run the post-CohortMembership command, dry-run
        call_command('post_cohort_membership_fix')

        # Verify nothing was changed in dry-run mode.
        self.assertEqual(self.user1.course_groups.count(), 2)  # CourseUserGroup has 2 entries for user1

        self.assertEqual(CohortMembership.objects.get(user=self.user2).course_user_group.name, 'Course1AutoGroup1')
        user2_cohorts = list(self.user2.course_groups.values_list('name', flat=True))
        self.assertEqual(user2_cohorts, ['Course1AutoGroup2'])  # CourseUserGroup and CohortMembership disagree

        # run the post-CohortMembership command, and commit it
        call_command('post_cohort_membership_fix', commit='commit')

        # verify that both databases agree about the (corrected) state of the memberships
        self.assertEqual(self.user1.course_groups.count(), 1)
        self.assertEqual(CohortMembership.objects.filter(user=self.user1).count(), 1)

        self.assertEqual(self.user2.course_groups.count(), 1)
        self.assertEqual(CohortMembership.objects.filter(user=self.user2).count(), 1)
        self.assertEqual(CohortMembership.objects.get(user=self.user2).course_user_group.name, 'Course1AutoGroup2')
        user2_cohorts = list(self.user2.course_groups.values_list('name', flat=True))
        self.assertEqual(user2_cohorts, ['Course1AutoGroup2'])
