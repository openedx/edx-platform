import django.test
from django.contrib.auth.models import User
from django.conf import settings

from override_settings import override_settings

from course_groups.models import CourseUserGroup
from course_groups.cohorts import get_cohort, get_course_cohorts

from xmodule.modulestore.django import modulestore

class TestCohorts(django.test.TestCase):

    def test_get_cohort(self):
        # Need to fix this, but after we're testing on staging.  (Looks like
        # problem is that when get_cohort internally tries to look up the
        # course.id, it fails, even though we loaded it through the modulestore.

        # Proper fix: give all tests a standard modulestore that uses the test
        # dir.
        course = modulestore().get_course("edX/toy/2012_Fall")
        self.assertEqual(course.id, "edX/toy/2012_Fall")

        user = User.objects.create(username="test", email="a@b.com")
        other_user = User.objects.create(username="test2", email="a2@b.com")

        self.assertIsNone(get_cohort(user, course.id), "No cohort created yet")

        cohort = CourseUserGroup.objects.create(name="TestCohort",
                                                course_id=course.id,
                               group_type=CourseUserGroup.COHORT)

        cohort.users.add(user)

        self.assertIsNone(get_cohort(user, course.id),
                          "Course isn't cohorted, so shouldn't have a cohort")

        # Make the course cohorted...
        course.metadata["cohort_config"] = {"cohorted": True}
        
        self.assertEquals(get_cohort(user, course.id).id, cohort.id,
                          "Should find the right cohort")

        self.assertEquals(get_cohort(other_user, course.id), None,
                          "other_user shouldn't have a cohort")


    def test_get_course_cohorts(self):
        course1_id = 'a/b/c'
        course2_id = 'e/f/g'

        # add some cohorts to course 1
        cohort = CourseUserGroup.objects.create(name="TestCohort",
                                                course_id=course1_id,
                                                group_type=CourseUserGroup.COHORT)

        cohort = CourseUserGroup.objects.create(name="TestCohort2",
                                                course_id=course1_id,
                                                group_type=CourseUserGroup.COHORT)


        # second course should have no cohorts
        self.assertEqual(get_course_cohorts(course2_id), [])

        cohorts = sorted([c.name for c in get_course_cohorts(course1_id)])
        self.assertEqual(cohorts, ['TestCohort', 'TestCohort2'])

