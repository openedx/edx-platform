"""
Test status utilities
"""
from unittest import TestCase
from unittest import mock

from django.conf import settings
from opaque_keys.edx.keys import CourseKey
from pytest import mark
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.catalog.tests.factories import (
    ProgramFactory,
)
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.enterprise_support.tests.factories import EnterpriseCustomerUserFactory

if settings.ROOT_URLCONF == 'lms.urls':
    from openedx.core.djangoapps.demographics.api.status import show_user_demographics, show_call_to_action_for_user
    from openedx.core.djangoapps.demographics.tests.factories import UserDemographicsFactory

MICROBACHELORS = 'microbachelors'


@skip_unless_lms
@mock.patch('openedx.core.djangoapps.programs.utils.get_programs_by_type')
class TestShowDemographics(SharedModuleStoreTestCase):
    """
    Tests for whether the demographics collection fields should be shown
    """
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
        assert not show_user_demographics(user=self.user)


@skip_unless_lms
@mark.django_db
class TestShowCallToAction(TestCase):
    """
    Tests for whether the demographics call to action should be shown
    """
    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_new_user(self):
        assert show_call_to_action_for_user(self.user)

    def test_existing_user_no_dismiss(self):
        user_demographics = UserDemographicsFactory.create(user=self.user)
        assert user_demographics.show_call_to_action
        assert show_call_to_action_for_user(self.user)

    def test_existing_user_dismissed(self):
        user_demographics = UserDemographicsFactory.create(user=self.user)
        user_demographics.show_call_to_action = False
        user_demographics.save()
        assert not user_demographics.show_call_to_action
        assert not show_call_to_action_for_user(self.user)
