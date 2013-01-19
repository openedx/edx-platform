from django.contrib.auth.models import User
from nose.tools import assert_equals

from course_groups.models import CourseUserGroup, get_cohort

def test_get_cohort():
    course_id = "a/b/c"
    cohort = CourseUserGroup.objects.create(name="TestCohort", course_id=course_id,
                           group_type=CourseUserGroup.COHORT)

    user = User.objects.create(username="test", email="a@b.com")
    other_user = User.objects.create(username="test2", email="a2@b.com")

    cohort.users.add(user)

    got = get_cohort(user, course_id)
    assert_equals(got.id, cohort.id, "Should find the right cohort")

    got = get_cohort(other_user, course_id)
    assert_equals(got, None, "other_user shouldn't have a cohort")

