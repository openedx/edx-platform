"""
Test status utilities
"""
import mock
from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from opaque_keys.edx.keys import CourseKey
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase, TEST_DATA_SPLIT_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory

from openedx.core.djangoapps.catalog.tests.factories import (
    ProgramFactory,
)
from openedx.core.djangoapps.demographics.api.status import show_user_demographics
from openedx.features.enterprise_support.tests.factories import EnterpriseCustomerUserFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms

MICROBACHELORS = 'microbachelors'


@skip_unless_lms
@mock.patch('openedx.core.djangoapps.programs.utils.get_programs_by_type')
class TestShowDemographics(SharedModuleStoreTestCase):
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.store = modulestore()
        cls.user = UserFactory()
        cls.program = ProgramFactory(type=MICROBACHELORS)
        cls.catalog_course_run = cls.program['courses'][0]['course_runs'][0]
        cls.course_key = CourseKey.from_string(cls.catalog_course_run['key'])
        cls.course_run = CourseFactory.create(
            org=cls.course_key.org,
            number=cls.course_key.course,
            run=cls.course_key.run,
            modulestore=cls.store,
        )
        CourseModeFactory.create(course_id=cls.course_run.id, mode_slug=CourseMode.VERIFIED)

    def test_user_enterprise(self, mock_get_programs_by_type):
        mock_get_programs_by_type.return_value = [self.program]
        EnterpriseCustomerUserFactory.create(user_id=self.user.id)
        self.assertFalse(show_user_demographics(user=self.user))
