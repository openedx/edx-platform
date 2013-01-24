import django.test
from django.contrib.auth.models import User

from course_groups.models import CourseUserGroup
from course_groups.cohorts import get_cohort, get_course_cohorts


class TestCohorts(django.test.TestCase):

    def test_get_cohort(self):
        course_id = "a/b/c"
        cohort = CourseUserGroup.objects.create(name="TestCohort", course_id=course_id,
                               group_type=CourseUserGroup.COHORT)

        user = User.objects.create(username="test", email="a@b.com")
        other_user = User.objects.create(username="test2", email="a2@b.com")

        cohort.users.add(user)

        got = get_cohort(user, course_id)
        self.assertEquals(got.id, cohort.id, "Should find the right cohort")

        got = get_cohort(other_user, course_id)
        self.assertEquals(got, None, "other_user shouldn't have a cohort")


    def test_get_course_cohorts(self):
        course1_id = "a/b/c"
        course2_id = "e/f/g"

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

