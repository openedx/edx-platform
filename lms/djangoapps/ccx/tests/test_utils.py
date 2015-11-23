"""
test utils
"""
from nose.plugins.attrib import attr

from lms.djangoapps.ccx.tests.factories import CcxFactory
from student.roles import CourseCcxCoachRole
from student.tests.factories import (
    AdminFactory,
)
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE)
from xmodule.modulestore.tests.factories import CourseFactory

from ccx_keys.locator import CCXLocator


@attr('shard_1')
class TestGetCCXFromCCXLocator(ModuleStoreTestCase):
    """Verify that get_ccx_from_ccx_locator functions properly"""
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """Set up a course, coach, ccx and user"""
        super(TestGetCCXFromCCXLocator, self).setUp()
        self.course = CourseFactory.create()
        coach = self.coach = AdminFactory.create()
        role = CourseCcxCoachRole(self.course.id)
        role.add_users(coach)

    def call_fut(self, course_id):
        """call the function under test in this test case"""
        from lms.djangoapps.ccx.utils import get_ccx_from_ccx_locator
        return get_ccx_from_ccx_locator(course_id)

    def test_non_ccx_locator(self):
        """verify that nothing is returned if locator is not a ccx locator
        """
        result = self.call_fut(self.course.id)
        self.assertEqual(result, None)

    def test_ccx_locator(self):
        """verify that the ccx is retuned if using a ccx locator
        """
        ccx = CcxFactory(course_id=self.course.id, coach=self.coach)
        course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        result = self.call_fut(course_key)
        self.assertEqual(result, ccx)
