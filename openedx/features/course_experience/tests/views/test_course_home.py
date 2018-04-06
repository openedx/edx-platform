# coding=utf-8
"""
Tests for the course home page.
"""
from datetime import datetime, timedelta

import ddt
import mock
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.utils.http import urlquote_plus
from django.utils.timezone import now
from pytz import UTC
from waffle.models import Flag
from waffle.testutils import override_flag

from course_modes.models import CourseMode
from courseware.tests.factories import StaffFactory
from lms.djangoapps.commerce.models import CommerceConfiguration
from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.course_goals.api import add_course_goal, remove_course_goal
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES, override_waffle_flag
from openedx.features.course_experience import (
    SHOW_REVIEWS_TOOL_FLAG,
    SHOW_UPGRADE_MSG_ON_COURSE_HOME,
    UNIFIED_COURSE_TAB_FLAG
)
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from util.date_utils import strftime_localized
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import CourseUserType, ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls

from ... import COURSE_PRE_START_ACCESS_FLAG, ENABLE_COURSE_GOALS
from .helpers import add_course_mode
from .test_course_updates import create_course_update, remove_course_updates

TEST_PASSWORD = 'test'
TEST_CHAPTER_NAME = 'Test Chapter'
TEST_WELCOME_MESSAGE = '<h2>Welcome!</h2>'
TEST_UPDATE_MESSAGE = '<h2>Test Update!</h2>'
TEST_COURSE_UPDATES_TOOL = '/course/updates">'
TEST_COURSE_HOME_MESSAGE = 'course-message'
TEST_COURSE_HOME_MESSAGE_ANONYMOUS = '/login'
TEST_COURSE_HOME_MESSAGE_UNENROLLED = 'Enroll now'
TEST_COURSE_HOME_MESSAGE_PRE_START = 'Course starts in'
TEST_COURSE_GOAL_OPTIONS = 'goal-options-container'
TEST_COURSE_GOAL_UPDATE_FIELD = 'section-goals'
TEST_COURSE_GOAL_UPDATE_FIELD_HIDDEN = 'section-goals hidden'
COURSE_GOAL_DISMISS_OPTION = 'unsure'

QUERY_COUNT_TABLE_BLACKLIST = WAFFLE_TABLES


def course_home_url(course):
    """
    Returns the URL for the course's home page.

    Arguments:
        course (CourseDescriptor): The course being tested.
    """
    return course_home_url_from_string(unicode(course.id))


def course_home_url_from_string(course_key_string):
    """
    Returns the URL for the course's home page.

    Arguments:
        course_key_string (String): The course key as string.
    """
    return reverse(
        'openedx.course_experience.course_home',
        kwargs={
            'course_id': course_key_string,
        }
    )


class CourseHomePageTestCase(SharedModuleStoreTestCase):
    """
    Base class for testing the course home page.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up a course to be used for testing.
        """
        # setUpClassAndTestData() already calls setUpClass on SharedModuleStoreTestCase
        # pylint: disable=super-method-not-called
        with super(CourseHomePageTestCase, cls).setUpClassAndTestData():
            with cls.store.default_store(ModuleStoreEnum.Type.split):
                cls.course = CourseFactory.create(
                    org='edX',
                    number='test',
                    display_name='Test Course',
                    start=now() - timedelta(days=30),
                )
                with cls.store.bulk_operations(cls.course.id):
                    chapter = ItemFactory.create(
                        category='chapter',
                        parent_location=cls.course.location,
                        display_name=TEST_CHAPTER_NAME,
                    )
                    section = ItemFactory.create(category='sequential', parent_location=chapter.location)
                    section2 = ItemFactory.create(category='sequential', parent_location=chapter.location)
                    ItemFactory.create(category='vertical', parent_location=section.location)
                    ItemFactory.create(category='vertical', parent_location=section2.location)

    @classmethod
    def setUpTestData(cls):
        """Set up and enroll our fake user in the course."""
        cls.staff_user = StaffFactory(course_key=cls.course.id, password=TEST_PASSWORD)
        cls.user = UserFactory(password=TEST_PASSWORD)
        CourseEnrollment.enroll(cls.user, cls.course.id)

    def create_future_course(self, specific_date=None):
        """
        Creates and returns a course in the future.
        """
        return CourseFactory.create(
            display_name='Test Future Course',
            start=specific_date if specific_date else now() + timedelta(days=30),
        )


class TestCourseHomePage(CourseHomePageTestCase):
    def setUp(self):
        super(TestCourseHomePage, self).setUp()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    def tearDown(self):
        remove_course_updates(self.user, self.course)
        super(TestCourseHomePage, self).tearDown()

    def test_welcome_message_when_unified(self):
        # Create a welcome message
        create_course_update(self.course, self.user, TEST_WELCOME_MESSAGE)

        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertContains(response, TEST_WELCOME_MESSAGE, status_code=200)

    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=False)
    def test_welcome_message_when_not_unified(self):
        # Create a welcome message
        create_course_update(self.course, self.user, TEST_WELCOME_MESSAGE)

        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertNotContains(response, TEST_WELCOME_MESSAGE, status_code=200)

    def test_updates_tool_visibility(self):
        """
        Verify that the updates course tool is visible only when the course
        has one or more updates.
        """
        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertNotContains(response, TEST_COURSE_UPDATES_TOOL, status_code=200)

        create_course_update(self.course, self.user, TEST_UPDATE_MESSAGE)
        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertContains(response, TEST_COURSE_UPDATES_TOOL, status_code=200)

    def test_queries(self):
        """
        Verify that the view's query count doesn't regress.
        """
        # Pre-fetch the view to populate any caches
        course_home_url(self.course)

        # Fetch the view and verify the query counts
        with self.assertNumQueries(52, table_blacklist=QUERY_COUNT_TABLE_BLACKLIST):
            with check_mongo_calls(4):
                url = course_home_url(self.course)
                self.client.get(url)

    @mock.patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_start_date_handling(self):
        """
        Verify that the course home page handles start dates correctly.
        """
        # The course home page should 404 for a course starting in the future
        future_course = self.create_future_course(datetime(2030, 1, 1, tzinfo=UTC))
        url = course_home_url(future_course)
        response = self.client.get(url)
        self.assertRedirects(response, '/dashboard?notlive=Jan+01%2C+2030')

        # With the Waffle flag enabled, the course should be visible
        with override_flag(COURSE_PRE_START_ACCESS_FLAG.namespaced_flag_name, True):
            url = course_home_url(future_course)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)


@ddt.ddt
class TestCourseHomePageAccess(CourseHomePageTestCase):
    """
    Test access to the course home page.
    """

    def setUp(self):
        super(TestCourseHomePageAccess, self).setUp()

        # Make this a verified course so that an upgrade message might be shown
        add_course_mode(self.course, upgrade_deadline_expired=False)

        # Add a welcome message
        create_course_update(self.course, self.staff_user, TEST_WELCOME_MESSAGE)

    def tearDown(self):
        remove_course_updates(self.staff_user, self.course)
        super(TestCourseHomePageAccess, self).tearDown()

    @override_waffle_flag(SHOW_REVIEWS_TOOL_FLAG, active=True)
    @ddt.data(
        [CourseUserType.ANONYMOUS, 'To see course content'],
        [CourseUserType.ENROLLED, None],
        [CourseUserType.UNENROLLED, 'You must be enrolled in the course to see course content.'],
        [CourseUserType.UNENROLLED_STAFF, 'You must be enrolled in the course to see course content.'],
    )
    @ddt.unpack
    def test_home_page(self, user_type, expected_message):
        self.create_user_for_course(self.course, user_type)

        # Render the course home page
        url = course_home_url(self.course)
        response = self.client.get(url)

        # Verify that the course tools and dates are always shown
        self.assertContains(response, 'Course Tools')
        self.assertContains(response, 'Today is')

        # Verify that the outline, start button, course sock, and welcome message
        # are only shown to enrolled users.
        is_enrolled = user_type is CourseUserType.ENROLLED
        is_unenrolled_staff = user_type is CourseUserType.UNENROLLED_STAFF
        expected_count = 1 if (is_enrolled or is_unenrolled_staff) else 0
        self.assertContains(response, TEST_CHAPTER_NAME, count=expected_count)
        self.assertContains(response, 'Start Course', count=expected_count)
        self.assertContains(response, 'Learn About Verified Certificate', count=(1 if is_enrolled else 0))
        self.assertContains(response, TEST_WELCOME_MESSAGE, count=expected_count)

        # Verify that the expected message is shown to the user
        self.assertContains(response, '<div class="user-messages">', count=1 if expected_message else 0)
        if expected_message:
            self.assertContains(response, expected_message)

    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=False)
    @override_waffle_flag(SHOW_REVIEWS_TOOL_FLAG, active=True)
    @ddt.data(
        [CourseUserType.ANONYMOUS, 'To see course content'],
        [CourseUserType.ENROLLED, None],
        [CourseUserType.UNENROLLED, 'You must be enrolled in the course to see course content.'],
        [CourseUserType.UNENROLLED_STAFF, 'You must be enrolled in the course to see course content.'],
    )
    @ddt.unpack
    def test_home_page_not_unified(self, user_type, expected_message):
        """
        Verifies the course home tab when not unified.
        """
        self.create_user_for_course(self.course, user_type)

        # Render the course home page
        url = course_home_url(self.course)
        response = self.client.get(url)

        # Verify that the course tools and dates are always shown
        self.assertContains(response, 'Course Tools')
        self.assertContains(response, 'Today is')

        # Verify that welcome messages are never shown
        self.assertNotContains(response, TEST_WELCOME_MESSAGE)

        # Verify that the outline, start button, course sock, and welcome message
        # are only shown to enrolled users.
        is_enrolled = user_type is CourseUserType.ENROLLED
        is_unenrolled_staff = user_type is CourseUserType.UNENROLLED_STAFF
        expected_count = 1 if (is_enrolled or is_unenrolled_staff) else 0
        self.assertContains(response, TEST_CHAPTER_NAME, count=expected_count)
        self.assertContains(response, 'Start Course', count=expected_count)
        self.assertContains(response, 'Learn About Verified Certificate', count=(1 if is_enrolled else 0))

        # Verify that the expected message is shown to the user
        self.assertContains(response, '<div class="user-messages">', count=1 if expected_message else 0)
        if expected_message:
            self.assertContains(response, expected_message)

    def test_sign_in_button(self):
        """
        Verify that the sign in button will return to this page.
        """
        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertContains(response, '/login?next={url}'.format(url=urlquote_plus(url)))

    @mock.patch.dict(settings.FEATURES, {'DISABLE_START_DATES': False})
    def test_non_live_course(self):
        """
        Ensure that a user accessing a non-live course sees a redirect to
        the student dashboard, not a 404.
        """
        future_course = self.create_future_course()
        self.create_user_for_course(future_course, CourseUserType.ENROLLED)

        url = course_home_url(future_course)
        response = self.client.get(url)
        start_date = strftime_localized(future_course.start, 'SHORT_DATE')
        expected_params = QueryDict(mutable=True)
        expected_params['notlive'] = start_date
        expected_url = '{url}?{params}'.format(
            url=reverse('dashboard'),
            params=expected_params.urlencode()
        )
        self.assertRedirects(response, expected_url)

    @mock.patch.dict(settings.FEATURES, {'DISABLE_START_DATES': False})
    @mock.patch("util.date_utils.strftime_localized")
    def test_non_live_course_other_language(self, mock_strftime_localized):
        """
        Ensure that a user accessing a non-live course sees a redirect to
        the student dashboard, not a 404, even if the localized date is unicode
        """
        future_course = self.create_future_course()
        self.create_user_for_course(future_course, CourseUserType.ENROLLED)

        fake_unicode_start_time = u"üñîçø∂é_ßtå®t_tîµé"
        mock_strftime_localized.return_value = fake_unicode_start_time

        url = course_home_url(future_course)
        response = self.client.get(url)
        expected_params = QueryDict(mutable=True)
        expected_params['notlive'] = fake_unicode_start_time
        expected_url = u'{url}?{params}'.format(
            url=reverse('dashboard'),
            params=expected_params.urlencode()
        )
        self.assertRedirects(response, expected_url)

    def test_nonexistent_course(self):
        """
        Ensure a non-existent course results in a 404.
        """
        self.create_user_for_course(self.course, CourseUserType.ANONYMOUS)

        url = course_home_url_from_string('not/a/course')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @override_waffle_flag(COURSE_PRE_START_ACCESS_FLAG, active=True)
    def test_course_messaging(self):
        """
        Ensure that the following four use cases work as expected

        1) Anonymous users are shown a course message linking them to the login page
        2) Unenrolled users are shown a course message allowing them to enroll
        3) Enrolled users who show up on the course page after the course has begun
        are not shown a course message.
        4) Enrolled users who show up on the course page before the course begins
        are shown a message explaining when the course starts as well as a call to
        action button that allows them to add a calendar event.
        """
        # Verify that anonymous users are shown a login link in the course message
        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertContains(response, TEST_COURSE_HOME_MESSAGE)
        self.assertContains(response, TEST_COURSE_HOME_MESSAGE_ANONYMOUS)

        # Verify that unenrolled users are shown an enroll call to action message
        user = self.create_user_for_course(self.course, CourseUserType.UNENROLLED)
        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertContains(response, TEST_COURSE_HOME_MESSAGE)
        self.assertContains(response, TEST_COURSE_HOME_MESSAGE_UNENROLLED)

        # Verify that enrolled users are not shown any state warning message when enrolled and course has begun.
        CourseEnrollment.enroll(user, self.course.id)
        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertNotContains(response, TEST_COURSE_HOME_MESSAGE_ANONYMOUS)
        self.assertNotContains(response, TEST_COURSE_HOME_MESSAGE_UNENROLLED)
        self.assertNotContains(response, TEST_COURSE_HOME_MESSAGE_PRE_START)

        # Verify that enrolled users are shown 'days until start' message before start date
        future_course = self.create_future_course()
        CourseEnrollment.enroll(user, future_course.id)
        url = course_home_url(future_course)
        response = self.client.get(url)
        self.assertContains(response, TEST_COURSE_HOME_MESSAGE)
        self.assertContains(response, TEST_COURSE_HOME_MESSAGE_PRE_START)

    @override_waffle_flag(COURSE_PRE_START_ACCESS_FLAG, active=True)
    @override_waffle_flag(ENABLE_COURSE_GOALS, active=True)
    def test_course_goals(self):
        """
        Ensure that the following five use cases work as expected.

        1) Unenrolled users are not shown the set course goal message.
        2) Enrolled users are shown the set course goal message if they have not yet set a course goal.
        3) Enrolled users are not shown the set course goal message if they have set a course goal.
        4) Enrolled and verified users are not shown the set course goal message.
        5) Enrolled users are not shown the set course goal message in a course that cannot be verified.
        """
        # Create a course with a verified track.
        verifiable_course = CourseFactory.create()
        add_course_mode(verifiable_course, upgrade_deadline_expired=False)

        # Verify that unenrolled users are not shown the set course goal message.
        user = self.create_user_for_course(verifiable_course, CourseUserType.UNENROLLED)
        response = self.client.get(course_home_url(verifiable_course))
        self.assertNotContains(response, TEST_COURSE_GOAL_OPTIONS)

        # Verify that enrolled users are shown the set course goal message in a verified course.
        CourseEnrollment.enroll(user, verifiable_course.id)
        response = self.client.get(course_home_url(verifiable_course))
        self.assertContains(response, TEST_COURSE_GOAL_OPTIONS)

        # Verify that enrolled users that have set a course goal are not shown the set course goal message.
        add_course_goal(user, verifiable_course.id, COURSE_GOAL_DISMISS_OPTION)
        response = self.client.get(course_home_url(verifiable_course))
        self.assertNotContains(response, TEST_COURSE_GOAL_OPTIONS)

        # Verify that enrolled and verified users are not shown the set course goal message.
        remove_course_goal(user, str(verifiable_course.id))
        CourseEnrollment.enroll(user, verifiable_course.id, CourseMode.VERIFIED)
        response = self.client.get(course_home_url(verifiable_course))
        self.assertNotContains(response, TEST_COURSE_GOAL_OPTIONS)

        # Verify that enrolled users are not shown the set course goal message in an audit only course.
        audit_only_course = CourseFactory.create()
        CourseEnrollment.enroll(user, audit_only_course.id)
        response = self.client.get(course_home_url(audit_only_course))
        self.assertNotContains(response, TEST_COURSE_GOAL_OPTIONS)

    @override_waffle_flag(COURSE_PRE_START_ACCESS_FLAG, active=True)
    @override_waffle_flag(ENABLE_COURSE_GOALS, active=True)
    def test_course_goal_updates(self):
        """
        Ensure that the following five use cases work as expected.

        1) Unenrolled users are not shown the update goal selection field.
        2) Enrolled users are not shown the update goal selection field if they have not yet set a course goal.
        3) Enrolled users are shown the update goal selection field if they have set a course goal.
        4) Enrolled users in the verified track are shown the update goal selection field.
        """
        # Create a course with a verified track.
        verifiable_course = CourseFactory.create()
        add_course_mode(verifiable_course, upgrade_deadline_expired=False)

        # Verify that unenrolled users are not shown the update goal selection field.
        user = self.create_user_for_course(verifiable_course, CourseUserType.UNENROLLED)
        response = self.client.get(course_home_url(verifiable_course))
        self.assertNotContains(response, TEST_COURSE_GOAL_UPDATE_FIELD)

        # Verify that enrolled users that have not set a course goal are shown a hidden update goal selection field.
        enrollment = CourseEnrollment.enroll(user, verifiable_course.id)
        response = self.client.get(course_home_url(verifiable_course))
        self.assertContains(response, TEST_COURSE_GOAL_UPDATE_FIELD_HIDDEN)

        # Verify that enrolled users that have set a course goal are shown a visible update goal selection field.
        add_course_goal(user, verifiable_course.id, COURSE_GOAL_DISMISS_OPTION)
        response = self.client.get(course_home_url(verifiable_course))
        self.assertContains(response, TEST_COURSE_GOAL_UPDATE_FIELD)
        self.assertNotContains(response, TEST_COURSE_GOAL_UPDATE_FIELD_HIDDEN)

        # Verify that enrolled and verified users are shown the update goal selection
        CourseEnrollment.update_enrollment(enrollment, is_active=True, mode=CourseMode.VERIFIED)
        response = self.client.get(course_home_url(verifiable_course))
        self.assertContains(response, TEST_COURSE_GOAL_UPDATE_FIELD)
        self.assertNotContains(response, TEST_COURSE_GOAL_UPDATE_FIELD_HIDDEN)


class CourseHomeFragmentViewTests(ModuleStoreTestCase):
    CREATE_USER = False

    def setUp(self):
        super(CourseHomeFragmentViewTests, self).setUp()
        CommerceConfiguration.objects.create(checkout_on_ecommerce_service=True)

        end = now() + timedelta(days=30)
        self.course = CourseFactory(
            start=now() - timedelta(days=30),
            end=end,
        )
        self.url = course_home_url(self.course)

        CourseMode.objects.create(course_id=self.course.id, mode_slug=CourseMode.AUDIT)
        self.verified_mode = CourseMode.objects.create(
            course_id=self.course.id,
            mode_slug=CourseMode.VERIFIED,
            min_price=100,
            expiration_datetime=end,
            sku='test'
        )

        self.user = UserFactory()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

        name = SHOW_UPGRADE_MSG_ON_COURSE_HOME.waffle_namespace._namespaced_name(
            SHOW_UPGRADE_MSG_ON_COURSE_HOME.flag_name)
        self.flag, __ = Flag.objects.update_or_create(name=name, defaults={'everyone': True})

    def assert_upgrade_message_not_displayed(self):
        response = self.client.get(self.url)
        self.assertNotIn('section-upgrade', response.content)

    def assert_upgrade_message_displayed(self):
        response = self.client.get(self.url)
        self.assertIn('section-upgrade', response.content)
        url = EcommerceService().get_checkout_page_url(self.verified_mode.sku)
        self.assertIn('<a class="btn-brand btn-upgrade"', response.content)
        self.assertIn(url, response.content)
        self.assertIn('Upgrade (${price})'.format(price=self.verified_mode.min_price), response.content)

    def test_no_upgrade_message_if_logged_out(self):
        self.client.logout()
        self.assert_upgrade_message_not_displayed()

    def test_no_upgrade_message_if_not_enrolled(self):
        self.assertEqual(len(CourseEnrollment.enrollments_for_user(self.user)), 0)
        self.assert_upgrade_message_not_displayed()

    def test_no_upgrade_message_if_verified_track(self):
        CourseEnrollment.enroll(self.user, self.course.id, CourseMode.VERIFIED)
        self.assert_upgrade_message_not_displayed()

    def test_no_upgrade_message_if_upgrade_deadline_passed(self):
        self.verified_mode.expiration_datetime = now() - timedelta(days=20)
        self.verified_mode.save()
        self.assert_upgrade_message_not_displayed()

    def test_no_upgrade_message_if_flag_disabled(self):
        self.flag.everyone = False
        self.flag.save()
        CourseEnrollment.enroll(self.user, self.course.id, CourseMode.AUDIT)
        self.assert_upgrade_message_not_displayed()

    def test_display_upgrade_message_if_audit_and_deadline_not_passed(self):
        CourseEnrollment.enroll(self.user, self.course.id, CourseMode.AUDIT)
        self.assert_upgrade_message_displayed()
