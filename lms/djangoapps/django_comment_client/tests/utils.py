"""
Utilities for tests within the django_comment_client module.
"""
from mock import patch

from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from django_comment_common.models import Role
from django_comment_common.utils import seed_permissions_roles
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase


class CohortedTestCase(SharedModuleStoreTestCase):
    """
    Sets up a course with a student, a moderator and their cohorts.
    """
    @classmethod
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUpClass(cls):
        super(CohortedTestCase, cls).setUpClass()
        cls.course = CourseFactory.create(
            cohort_config={
                "cohorted": True,
                "cohorted_discussions": ["cohorted_topic"]
            }
        )
        cls.course.discussion_topics["cohorted topic"] = {"id": "cohorted_topic"}
        cls.course.discussion_topics["non-cohorted topic"] = {"id": "non_cohorted_topic"}
        fake_user_id = 1
        cls.store.update_item(cls.course, fake_user_id)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(CohortedTestCase, self).setUp()

        seed_permissions_roles(self.course.id)
        self.student = UserFactory.create()
        self.moderator = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)
        CourseEnrollmentFactory(user=self.moderator, course_id=self.course.id)
        self.moderator.roles.add(Role.objects.get(name="Moderator", course_id=self.course.id))
        self.student_cohort = CohortFactory.create(
            name="student_cohort",
            course_id=self.course.id,
            users=[self.student]
        )
        self.moderator_cohort = CohortFactory.create(
            name="moderator_cohort",
            course_id=self.course.id,
            users=[self.moderator]
        )
