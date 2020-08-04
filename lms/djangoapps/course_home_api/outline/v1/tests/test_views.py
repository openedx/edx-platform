"""
Tests for Outline Tab API in the Course Home API
"""

import ddt
from django.urls import reverse

from course_modes.models import CourseMode
from lms.djangoapps.course_home_api.tests.utils import BaseCourseHomeTests
from lms.djangoapps.course_home_api.toggles import COURSE_HOME_MICROFRONTEND, COURSE_HOME_MICROFRONTEND_OUTLINE_TAB
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from openedx.core.djangoapps.user_api.tests.factories import UserCourseTagFactory
from openedx.features.course_experience import COURSE_ENABLE_UNENROLLED_ACCESS_FLAG
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.course_module import COURSE_VISIBILITY_PUBLIC


@ddt.ddt
class OutlineTabTestViews(BaseCourseHomeTests):
    """
    Tests for the Outline Tab API
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('course-home-outline-tab', args=[self.course.id])

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    @ddt.data(CourseMode.AUDIT, CourseMode.VERIFIED)
    def test_get_authenticated_enrolled_user(self, enrollment_mode):
        CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        course_tools = response.data.get('course_tools')
        self.assertTrue(course_tools)
        self.assertEqual(course_tools[0]['analytics_id'], 'edx.bookmarks')

        dates_widget = response.data.get('dates_widget')
        self.assertTrue(dates_widget)
        date_blocks = dates_widget.get('course_date_blocks')
        self.assertTrue(all((block.get('title') != "") for block in date_blocks))
        self.assertTrue(all(block.get('date') for block in date_blocks))

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    def test_get_authenticated_user_not_enrolled(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        course_tools = response.data.get('course_tools')
        self.assertEqual(len(course_tools), 0)

        dates_widget = response.data.get('dates_widget')
        self.assertTrue(dates_widget)
        date_blocks = dates_widget.get('course_date_blocks')
        self.assertTrue(all((block.get('title') != "") for block in date_blocks))
        self.assertTrue(all(block.get('date') for block in date_blocks))

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    def test_get_unauthenticated_user(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    def test_masquerade(self):
        user = UserFactory()
        set_user_preference(user, 'time_zone', 'Asia/Tokyo')
        CourseEnrollment.enroll(user, self.course.id)

        self.switch_to_staff()  # needed for masquerade

        # Sanity check on our normal user
        self.assertEqual(self.client.get(self.url).data['dates_widget']['user_timezone'], None)

        # Now switch users and confirm we get a different result
        self.update_masquerade(username=user.username)
        self.assertEqual(self.client.get(self.url).data['dates_widget']['user_timezone'], 'Asia/Tokyo')

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    @ddt.data(
        (True, True, True, True),  # happy path
        (True, False, False, True),  # is enrolled
        (False, True, False, True),  # is staff
        (False, False, True, True),  # public visibility
        (False, False, False, False),  # no access
    )
    @ddt.unpack
    @COURSE_ENABLE_UNENROLLED_ACCESS_FLAG.override()
    def test_handouts(self, is_enrolled, is_staff, is_public, handouts_visible):
        if is_enrolled:
            CourseEnrollment.enroll(self.user, self.course.id)
        if is_staff:
            self.user.is_staff = True
            self.user.save()
        if is_public:
            self.course.course_visibility = COURSE_VISIBILITY_PUBLIC
            self.course = self.update_course(self.course, self.user.id)

        self.store.create_item(self.user.id, self.course.id, 'course_info', 'handouts', fields={'data': '<p>Hi</p>'})

        handouts_html = self.client.get(self.url).data['handouts_html']
        self.assertEqual(handouts_html, '<p>Hi</p>' if handouts_visible else '')

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    def test_get_unknown_course(self):
        url = reverse('course-home-outline-tab', args=['course-v1:unknown+course+2T2020'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=False)
    @ddt.data(CourseMode.AUDIT, CourseMode.VERIFIED)
    def test_waffle_flag_disabled(self, enrollment_mode):
        CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    @COURSE_HOME_MICROFRONTEND.override(active=True)
    @COURSE_HOME_MICROFRONTEND_OUTLINE_TAB.override(active=True)
    @ddt.data(True, False)
    def test_welcome_message(self, welcome_message_is_dismissed):
        self.store.create_item(
            self.user.id, self.course.id,
            'course_info',
            'updates',
            fields={
                'items': [{
                    'content': '<p>Welcome</p>',
                    'status': 'visible',
                    'date': 'July 23, 2020',
                    'id': 1
                }]
            }
        )
        UserCourseTagFactory(
            user=self.user,
            course_id=self.course.id,
            key='view-welcome-message',
            value=False if welcome_message_is_dismissed else True
        )
        welcome_message_html = self.client.get(self.url).data['welcome_message_html']
        self.assertEqual(welcome_message_html, None if welcome_message_is_dismissed else '<p>Welcome</p>')
