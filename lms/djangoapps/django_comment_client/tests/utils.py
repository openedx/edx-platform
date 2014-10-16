from django.test.utils import override_settings

from course_groups.models import CourseUserGroup
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from django_comment_common.models import Role
from django_comment_common.utils import seed_permissions_roles
from mock import patch
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class CohortedContentTestCase(ModuleStoreTestCase):
    """
    Sets up a course with a student, a moderator and their cohorts.
    """
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(CohortedContentTestCase, self).setUp()

        self.course = CourseFactory.create(
            discussion_topics={
                "cohorted topic": {"id": "cohorted_topic"},
                "non-cohorted topic": {"id": "non_cohorted_topic"},
            },
            cohort_config={
                "cohorted": True,
                "cohorted_discussions": ["cohorted_topic"]
            }
        )
        self.student_cohort = CourseUserGroup.objects.create(
            name="student_cohort",
            course_id=self.course.id,
            group_type=CourseUserGroup.COHORT
        )
        self.moderator_cohort = CourseUserGroup.objects.create(
            name="moderator_cohort",
            course_id=self.course.id,
            group_type=CourseUserGroup.COHORT
        )

        seed_permissions_roles(self.course.id)
        self.student = UserFactory.create()
        self.moderator = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)
        CourseEnrollmentFactory(user=self.moderator, course_id=self.course.id)
        self.moderator.roles.add(Role.objects.get(name="Moderator", course_id=self.course.id))
        self.student_cohort.users.add(self.student)
        self.moderator_cohort.users.add(self.moderator)
