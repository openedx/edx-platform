"""
Tests for Discussion REST API utils.
"""

from datetime import datetime, timedelta

from pytz import UTC

from common.djangoapps.student.roles import CourseStaffRole, CourseInstructorRole
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.discussion.django_comment_client.tests.factories import RoleFactory
from lms.djangoapps.discussion.rest_api.utils import (
    discussion_open_for_user,
    get_course_ta_users_list,
    get_course_staff_users_list,
    get_moderator_users_list,
)


class DiscussionAPIUtilsTestCase(ModuleStoreTestCase):
    """
    Base test-case class for utils for Discussion REST API.
    """
    CREATE_USER = False

    def setUp(self):
        super().setUp()     # lint-amnesty, pylint: disable=super-with-arguments

        self.course = CourseFactory.create()
        self.course.discussion_blackouts = [datetime.now(UTC) - timedelta(days=3),
                                            datetime.now(UTC) + timedelta(days=3)]
        self.student_role = RoleFactory(name='Student', course_id=self.course.id)
        self.moderator_role = RoleFactory(name='Moderator', course_id=self.course.id)
        self.community_ta_role = RoleFactory(name='Community TA', course_id=self.course.id)
        self.group_community_ta_role = RoleFactory(name='Group Moderator', course_id=self.course.id)

        self.student = UserFactory(username='student', email='student@edx.org')
        self.student_enrollment = CourseEnrollmentFactory(user=self.student)
        self.student_role.users.add(self.student)

        self.moderator = UserFactory(username='moderator', email='staff@edx.org', is_staff=True)
        self.moderator_enrollment = CourseEnrollmentFactory(user=self.moderator)
        self.moderator_role.users.add(self.moderator)

        self.community_ta = UserFactory(username='community_ta1', email='community_ta1@edx.org')
        self.community_ta_role.users.add(self.community_ta)

        self.group_community_ta = UserFactory(username='group_community_ta1', email='group_community_ta1@edx.org')
        self.group_community_ta_role.users.add(self.group_community_ta)

        self.course_staff_user = UserFactory(username='course_staff_user1', email='course_staff_user1@edx.org')
        self.course_instructor_user = UserFactory(username='course_instructor_user1',
                                                  email='course_instructor_user1@edx.org')
        CourseStaffRole(course_key=self.course.id).add_users(self.course_staff_user)
        CourseInstructorRole(course_key=self.course.id).add_users(self.course_instructor_user)

    def test_discussion_open_for_user(self):
        self.assertFalse(discussion_open_for_user(self.course, self.student))
        self.assertTrue(discussion_open_for_user(self.course, self.moderator))
        self.assertTrue(discussion_open_for_user(self.course, self.community_ta))

    def test_course_staff_users_list(self):
        assert len(get_course_staff_users_list(self.course.id)) == 2

    def test_course_moderator_users_list(self):
        assert len(get_moderator_users_list(self.course.id)) == 1

    def test_course_ta_users_list(self):
        ta_user_list = get_course_ta_users_list(self.course.id)
        assert len(ta_user_list) == 2
