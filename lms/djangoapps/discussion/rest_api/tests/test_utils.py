"""
Tests for Discussion REST API utils.
"""

from datetime import datetime, timedelta

from pytz import UTC

from common.djangoapps.student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from lms.djangoapps.discussion.django_comment_client.tests.factories import RoleFactory
from lms.djangoapps.discussion.rest_api.utils import discussion_open_for_user
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order


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
        self.student = UserFactory(username='student', email='student@edx.org')
        self.student_enrollment = CourseEnrollmentFactory(user=self.student)
        self.student_role.users.add(self.student)
        self.moderator = UserFactory(username='moderator', email='staff@edx.org', is_staff=True)
        self.moderator_enrollment = CourseEnrollmentFactory(user=self.moderator)
        self.moderator_role.users.add(self.moderator)
        self.community_ta = UserFactory(username='community_ta1', email='community_ta1@edx.org')
        self.community_ta_role.users.add(self.community_ta)

    def test_discussion_open_for_user(self):
        self.assertFalse(discussion_open_for_user(self.course, self.student))
        self.assertTrue(discussion_open_for_user(self.course, self.moderator))
        self.assertTrue(discussion_open_for_user(self.course, self.community_ta))
