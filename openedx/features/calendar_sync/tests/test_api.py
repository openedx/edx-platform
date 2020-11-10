""" Tests for the Calendar Sync API """


from openedx.features.calendar_sync.api import subscribe_user_to_calendar, unsubscribe_user_to_calendar
from openedx.features.calendar_sync.models import UserCalendarSyncConfig
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

TEST_PASSWORD = 'test'


class TestCalendarSyncAPI(SharedModuleStoreTestCase):
    """ Tests for the Calendar Sync API """
    @classmethod
    def setUpClass(cls):
        """ Set up any course data """
        super(TestCalendarSyncAPI, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.course_key = cls.course.id

    def setUp(self):
        super(TestCalendarSyncAPI, self).setUp()
        self.user = UserFactory(password=TEST_PASSWORD)

    def test_subscribe_to_calendar(self):
        self.assertEqual(UserCalendarSyncConfig.objects.count(), 0)
        subscribe_user_to_calendar(self.user, self.course_key)
        self.assertEqual(UserCalendarSyncConfig.objects.count(), 1)
        self.assertTrue(UserCalendarSyncConfig.is_enabled_for_course(self.user, self.course_key))

    def test_unsubscribe_to_calendar(self):
        self.assertEqual(UserCalendarSyncConfig.objects.count(), 0)
        unsubscribe_user_to_calendar(self.user, self.course_key)
        self.assertEqual(UserCalendarSyncConfig.objects.count(), 0)

        UserCalendarSyncConfig.objects.create(user=self.user, course_key=self.course_key, enabled=True)
        self.assertTrue(UserCalendarSyncConfig.is_enabled_for_course(self.user, self.course_key))
        unsubscribe_user_to_calendar(self.user, self.course_key)
        self.assertFalse(UserCalendarSyncConfig.is_enabled_for_course(self.user, self.course_key))
