from unittest.mock import Mock, patch

import ddt
from django.contrib.auth.models import User
from lms.djangoapps.course_blocks.transformers.tests.helpers import ModuleStoreTestCase
from lms.djangoapps.instructor_task.tasks_helper.module_state import _get_modules_to_update
from openedx.core.djangoapps.appsembler.api.tests.factories import OrganizationCourseFactory
from openedx.core.djangoapps.appsembler.multi_tenant_emails.tests.test_utils import (
    create_org_user,
    with_organization_context,
)
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class TestGetModulesToUpdate(ModuleStoreTestCase):
    """
    _get_modules_to_update is called by perform_module_state_update which is called by instructor tasks to update
    and/or override scores. We don't need to test the whole cycle, we just need to fix the bug where tasks are
    failing because (get_student internal method of _get_modules_to_update) is failing with multi-tenant
    """
    def setUp(self):
        """
        Initialize tests data
        """
        super(TestGetModulesToUpdate, self).setUp()
        with with_organization_context(site_color='purple') as purple_org:
            self.user = create_org_user(purple_org)
        self.course = CourseFactory.create()
        OrganizationCourseFactory(organization=purple_org, course_id=str(self.course.id))

    @patch(
        'lms.djangoapps.courseware.models.StudentModule.get_state_by_params',
        Mock(return_value='dummy_module')
    )
    @ddt.data(True, False)
    def test_get_modules_to_update(self, option_value):
        """
        Verify that _get_modules_to_update works fine
        """
        with patch.dict('django.conf.settings.FEATURES', {'APPSEMBLER_MULTI_TENANT_EMAILS': option_value}):
            self.assertEquals(
                _get_modules_to_update(self.course.id, 'dummy_location', self.user.email, None),
                'dummy_module'
            )
            self.assertEquals(
                _get_modules_to_update(self.course.id, 'dummy_location', self.user.username, None),
                'dummy_module'
            )

    @patch(
        'lms.djangoapps.courseware.models.StudentModule.get_state_by_params',
        Mock(return_value='dummy_module')
    )
    @ddt.data(True, False)
    def test_get_modules_to_update_bad_user_identifier(self, option_value):
        """
        Verify that _get_modules_to_update will fail if a bad user identifier is sent to it
        """
        with patch.dict('django.conf.settings.FEATURES', {'APPSEMBLER_MULTI_TENANT_EMAILS': option_value}):
            with self.assertRaises(User.DoesNotExist):
                _get_modules_to_update(self.course.id, 'dummy_location', 'bad_user', None)
