"""
Base classes for labster tests.
"""
from datetime import datetime, timedelta

import mock
from django.test.utils import override_settings
from django.utils.timezone import UTC

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, TEST_DATA_SPLIT_MODULESTORE
from ccx.tests.factories import CcxFactory
from ccx_keys.locator import CCXLocator
from student.roles import CourseCcxCoachRole
from student.tests.factories import UserFactory, AdminFactory
from lms.djangoapps.courseware.tests.test_field_overrides import inject_field_overrides
from lms.djangoapps.ccx.tests.test_views import iter_blocks
from request_cache.middleware import RequestCache
from courseware.field_overrides import OverrideFieldData  # pylint: disable=import-error


@override_settings(
    FIELD_OVERRIDE_PROVIDERS=('ccx.overrides.CustomCoursesForEdxOverrideProvider',),
)
class CCXCourseTestBase(ModuleStoreTestCase):

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """
        Set up the test data used in the specific tests
        """
        super(CCXCourseTestBase, self).setUp()

        self.consumer_keys = ['123', '789']
        self.lti_passports = self.make_lti_passports(self.consumer_keys)

        start_datetime = datetime.now(UTC()) - timedelta(days=1)
        end_datetime = datetime.now(UTC()) + timedelta(days=1)

        self.course = CourseFactory.create(
            enable_ccx=True,
            display_name='Test Course',
            lti_passports=self.lti_passports,
            start=start_datetime,
            end=end_datetime
        )
        # Create instructor account
        self.user = UserFactory.create()
        self.make_coach()
        self.ccx = self.make_ccx()
        self.ccx_key = CCXLocator.from_course_locator(self.course.id, self.ccx.id)

        patch = mock.patch('ccx.overrides.get_current_ccx')
        self.get_ccx = get_ccx = patch.start()
        get_ccx.return_value = self.ccx
        self.addCleanup(patch.stop)

        self.addCleanup(RequestCache.clear_request_cache)


    def inject_field_overrides(self):
        """
        Apparently the test harness doesn't use LmsFieldStorage, and I'm
        not sure if there's a way to poke the test harness to do so.  So,
        we'll just inject the override field storage in this brute force
        manner.
        """
        inject_field_overrides(iter_blocks(self.ccx.course), self.course, AdminFactory.create())

        def cleanup_provider_classes():
            """
            After everything is done, clean up by un-doing the change to the
            OverrideFieldData object that is done during the wrap method.
            """
            OverrideFieldData.provider_classes = None
        self.addCleanup(cleanup_provider_classes)

    def make_lti_passports(self, consumer_keys):
        """
        Create lti passports.
        """
        return [
            ':'.join(['TEST-' + str(i), k, '__secret_key__'])
            for i, k in enumerate(consumer_keys)
        ]

    def make_coach(self):
        """
        Create coach user.
        """
        role = CourseCcxCoachRole(self.course.id)
        role.add_users(self.user)

    def make_ccx(self):
        """
        Create ccx.
        """
        return CcxFactory(course_id=self.course.id, coach=self.user)
