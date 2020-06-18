"""
Unit tests for the calendar sync plugins.
"""


import crum
import ddt
from django.test import RequestFactory

from xmodule.modulestore.tests.django_utils import CourseUserType, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.features.calendar_sync.plugins import CalendarSyncToggleTool
from openedx.features.course_experience import CALENDAR_SYNC_FLAG, RELATIVE_DATES_FLAG


@ddt.ddt
class TestCalendarSyncToggleTool(SharedModuleStoreTestCase):
    """
    Test the calendar sync toggle tool.
    """
    @classmethod
    def setUpClass(cls):
        """ Set up any course data """
        super(TestCalendarSyncToggleTool, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.course_key = cls.course.id

    @ddt.data(
        [CourseUserType.ANONYMOUS, False],
        [CourseUserType.ENROLLED, True],
        [CourseUserType.UNENROLLED, False],
        [CourseUserType.UNENROLLED_STAFF, False],
    )
    @ddt.unpack
    @override_waffle_flag(CALENDAR_SYNC_FLAG, active=True)
    @RELATIVE_DATES_FLAG.override(active=True)
    def test_calendar_sync_toggle_tool_is_enabled(self, user_type, should_be_enabled):
        request = RequestFactory().request()
        request.user = self.create_user_for_course(self.course, user_type)
        self.addCleanup(crum.set_current_request, None)
        crum.set_current_request(request)
        self.assertEqual(CalendarSyncToggleTool.is_enabled(request, self.course.id), should_be_enabled)
