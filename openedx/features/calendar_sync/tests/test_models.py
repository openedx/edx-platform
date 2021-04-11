""" Tests for the Calendar Sync models """


from openedx.features.calendar_sync.models import UserCalendarSyncConfig
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

TEST_PASSWORD = 'test'


class TestUserCalendarSyncConfig(SharedModuleStoreTestCase):
    """ Tests for the UserCalendarSyncConfig model """
    @classmethod
    def setUpClass(cls):
        """ Set up any course data """
        super(TestUserCalendarSyncConfig, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.course_key = cls.course.id

    def setUp(self):
        super(TestUserCalendarSyncConfig, self).setUp()
        self.user = UserFactory(password=TEST_PASSWORD)

    def test_is_enabled_for_course(self):
        # Calendar Sync Config does not exist and returns False
        self.assertFalse(UserCalendarSyncConfig.is_enabled_for_course(self.user, self.course_key))

        # Default value for enabled is False
        UserCalendarSyncConfig.objects.create(user=self.user, course_key=self.course_key)
        self.assertFalse(UserCalendarSyncConfig.is_enabled_for_course(self.user, self.course_key))

        UserCalendarSyncConfig.objects.filter(user=self.user, course_key=self.course_key).update(enabled=True)
        self.assertTrue(UserCalendarSyncConfig.is_enabled_for_course(self.user, self.course_key))
