"""
Base classes for labster tests.
"""
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, TEST_DATA_SPLIT_MODULESTORE
from ccx.tests.factories import CcxFactory
from ccx_keys.locator import CCXLocator
from student.roles import CourseCcxCoachRole
from student.tests.factories import UserFactory


class LTITestBase(ModuleStoreTestCase):

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """
        Set up the test data used in the specific tests
        """
        super(LTITestBase, self).setUp()

        self.consumer_keys = ['123', '789']
        self.lti_passports = self.make_lti_passports(self.consumer_keys)
        self.course = CourseFactory.create(
            enable_ccx=True,
            display_name='Test Course', lti_passports=self.lti_passports
        )
        # Create instructor account
        self.user = UserFactory.create()
        self.make_coach()
        self.ccx = self.make_ccx()
        self.ccx_key = CCXLocator.from_course_locator(self.course.id, self.ccx.id)

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
