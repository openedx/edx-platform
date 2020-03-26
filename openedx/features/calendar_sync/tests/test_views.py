"""
Tests for Calendar Sync views.
"""


import ddt

from django.test import TestCase
from django.urls import reverse

from lms.djangoapps.courseware.tests.factories import UserFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.features.calendar_sync.api import SUBSCRIBE, UNSUBSCRIBE
from openedx.features.calendar_sync.views.management import compose_calendar_sync_email
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

TEST_PASSWORD = 'test'


@ddt.ddt
class TestCalendarSyncView(SharedModuleStoreTestCase, TestCase):
    """Tests for the calendar sync view."""
    @classmethod
    def setUpClass(cls):
        """ Set up any course data """
        super(TestCalendarSyncView, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestCalendarSyncView, self).setUp()
        self.user = self.create_user_for_course(self.course)
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.calendar_sync_url = reverse('openedx.calendar_sync', args=[self.course.id])

    @ddt.data(
        # Redirect on successful subscribe
        [{'tool_data': "{{'toggle_data': '{}'}}".format(SUBSCRIBE)}, 302, ''],
        # Redirect on successful unsubscribe
        [{'tool_data': "{{'toggle_data': '{}'}}".format(UNSUBSCRIBE)}, 302, ''],
        # 422 on unknown toggle_data
        [{'tool_data': "{{'toggle_data': '{}'}}".format('gibberish')}, 422,
            'Toggle data was not provided or had unknown value.'],
        # 422 on no toggle_data
        [{'tool_data': "{{'random_data': '{}'}}".format('gibberish')}, 422,
            'Toggle data was not provided or had unknown value.'],
        # 422 on no tool_data
        [{'nonsense': "{{'random_data': '{}'}}".format('gibberish')}, 422, 'Tool data was not provided.'],
    )
    @ddt.unpack
    def test_course_dates_fragment(self, data, expected_status_code, contained_text):
        response = self.client.post(self.calendar_sync_url, data)
        self.assertEqual(response.status_code, expected_status_code)
        self.assertIn(contained_text, str(response.content))


@ddt.ddt
class CalendarSyncEmailTestCase(TestCase):
    """
    Test for send activation email to user
    """

    @ddt.data(False, True)
    def test_compose_calendar_sync_email(self, is_update):
        """
        Tests that attributes of the message are being filled correctly in compose_activation_email
        """
        user = UserFactory()
        course_overview = CourseOverviewFactory()
        course_name = course_overview.display_name
        if is_update:
            calendar_sync_subject = 'Updates for Your {course} Schedule'.format(course=course_name)
            calendar_sync_headline = 'Update Your Calendar'
            calendar_sync_body = ('Your assignment due dates for {course} were recently adjusted. Update your calendar'
                                  'with your new schedule to ensure that you stay on track!').format(course=course_name)
        else:
            calendar_sync_subject = 'Stay on Track'
            calendar_sync_headline = 'Mark Your Calendar'
            calendar_sync_body = (
                'Sticking to a schedule is the best way to ensure that you successfully complete your '
                'self-paced course. This schedule of assignment due dates for {course} will help you '
                'stay on track!'.format(course=course_name))

        msg = compose_calendar_sync_email(user, course_overview, is_update)

        self.assertEqual(msg.context['calendar_sync_subject'], calendar_sync_subject)
        self.assertEqual(msg.context['calendar_sync_headline'], calendar_sync_headline)
        self.assertEqual(msg.context['calendar_sync_body'], calendar_sync_body)
        self.assertEqual(msg.recipient.username, user.username)
        self.assertEqual(msg.recipient.email_address, user.email)
