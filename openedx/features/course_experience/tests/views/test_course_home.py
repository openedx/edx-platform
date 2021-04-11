# coding=utf-8
"""
Tests for the course home page.
"""


from datetime import datetime, timedelta

import ddt
import mock
import six
from django.conf import settings
from django.http import QueryDict
from django.urls import reverse
from django.utils.http import urlquote_plus
from django.utils.timezone import now
from edx_toggles.toggles.testutils import override_waffle_flag
from pytz import UTC
from waffle.models import Flag
from waffle.testutils import override_flag

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.experiments.models import ExperimentData
from lms.djangoapps.commerce.models import CommerceConfiguration
from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.course_goals.api import add_course_goal, remove_course_goal
from lms.djangoapps.courseware.tests.factories import (
    BetaTesterFactory,
    GlobalStaffFactory,
    InstructorFactory,
    OrgInstructorFactory,
    OrgStaffFactory,
    StaffFactory
)
from lms.djangoapps.courseware.tests.helpers import get_expiration_banner_text
from lms.djangoapps.courseware.utils import verified_upgrade_deadline_link
from lms.djangoapps.discussion.django_comment_client.tests.factories import RoleFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.dark_lang.models import DarkLangConfig
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_GROUP_MODERATOR,
    FORUM_ROLE_MODERATOR
)
from openedx.core.djangoapps.schedules.tests.factories import ScheduleFactory
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES
from openedx.core.djangolib.markup import HTML
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from openedx.features.course_experience import (
    COURSE_ENABLE_UNENROLLED_ACCESS_FLAG,
    DISABLE_UNIFIED_COURSE_TAB_FLAG,
    SHOW_REVIEWS_TOOL_FLAG,
    SHOW_UPGRADE_MSG_ON_COURSE_HOME
)
from openedx.features.discounts.applicability import get_discount_expiration_date
from openedx.features.discounts.utils import REV1008_EXPERIMENT_ID, format_strikeout_price
from common.djangoapps.student.models import CourseEnrollment, FBEEnrollmentExclusion
from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.util.date_utils import strftime_localized
from xmodule.course_module import COURSE_VISIBILITY_PRIVATE, COURSE_VISIBILITY_PUBLIC, COURSE_VISIBILITY_PUBLIC_OUTLINE
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import CourseUserType, ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls

from ... import COURSE_PRE_START_ACCESS_FLAG, ENABLE_COURSE_GOALS
from .helpers import add_course_mode, remove_course_mode
from .test_course_updates import create_course_update, remove_course_updates

TEST_PASSWORD = 'test'
TEST_CHAPTER_NAME = 'Test Chapter'
TEST_COURSE_TOOLS = 'Course Tools'
TEST_BANNER_CLASS = '<div class="course-expiration-message">'
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
THREE_YEARS_AGO = now() - timedelta(days=(365 * 3))

QUERY_COUNT_TABLE_BLACKLIST = WAFFLE_TABLES


def course_home_url(course):
    """
    Returns the URL for the course's home page.

    Arguments:
        course (CourseDescriptor): The course being tested.
    """
    return course_home_url_from_string(six.text_type(course.id))


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
        # pylint: disable=super-method-not-called
        with cls.setUpClassAndTestData():
            with cls.store.default_store(ModuleStoreEnum.Type.split):
                cls.course = CourseFactory.create(
                    org='edX',
                    number='test',
                    display_name='Test Course',
                    start=now() - timedelta(days=30),
                    metadata={"invitation_only": False}
                )
                cls.private_course = CourseFactory.create(
                    org='edX',
                    number='test',
                    display_name='Test Private Course',
                    start=now() - timedelta(days=30),
                    metadata={"invitation_only": True}
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
        super(CourseHomePageTestCase, cls).setUpTestData()
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

    @override_waffle_flag(DISABLE_UNIFIED_COURSE_TAB_FLAG, active=True)
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
        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1, tzinfo=UTC))
        # Pre-fetch the view to populate any caches
        course_home_url(self.course)

        # Fetch the view and verify the query counts
        # TODO: decrease query count as part of REVO-28
        with self.assertNumQueries(73, table_blacklist=QUERY_COUNT_TABLE_BLACKLIST):
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
        add_course_mode(self.course, mode_slug=CourseMode.AUDIT)
        add_course_mode(self.course)

        # Add a welcome message
        create_course_update(self.course, self.staff_user, TEST_WELCOME_MESSAGE)

    def tearDown(self):
        remove_course_updates(self.staff_user, self.course)
        super(TestCourseHomePageAccess, self).tearDown()

    @override_waffle_flag(SHOW_REVIEWS_TOOL_FLAG, active=True)
    @ddt.data(
        [False, COURSE_VISIBILITY_PRIVATE, CourseUserType.ANONYMOUS, True, False],
        [False, COURSE_VISIBILITY_PUBLIC_OUTLINE, CourseUserType.ANONYMOUS, True, False],
        [False, COURSE_VISIBILITY_PUBLIC, CourseUserType.ANONYMOUS, True, False],
        [True, COURSE_VISIBILITY_PRIVATE, CourseUserType.ANONYMOUS, True, False],
        [True, COURSE_VISIBILITY_PUBLIC_OUTLINE, CourseUserType.ANONYMOUS, True, True],
        [True, COURSE_VISIBILITY_PUBLIC, CourseUserType.ANONYMOUS, True, True],

        [False, COURSE_VISIBILITY_PRIVATE, CourseUserType.UNENROLLED, True, False],
        [False, COURSE_VISIBILITY_PUBLIC_OUTLINE, CourseUserType.UNENROLLED, True, False],
        [False, COURSE_VISIBILITY_PUBLIC, CourseUserType.UNENROLLED, True, False],
        [True, COURSE_VISIBILITY_PRIVATE, CourseUserType.UNENROLLED, True, False],
        [True, COURSE_VISIBILITY_PUBLIC_OUTLINE, CourseUserType.UNENROLLED, True, True],
        [True, COURSE_VISIBILITY_PUBLIC, CourseUserType.UNENROLLED, True, True],

        [False, COURSE_VISIBILITY_PRIVATE, CourseUserType.ENROLLED, False, True],
        [True, COURSE_VISIBILITY_PRIVATE, CourseUserType.ENROLLED, False, True],
        [True, COURSE_VISIBILITY_PUBLIC_OUTLINE, CourseUserType.ENROLLED, False, True],
        [True, COURSE_VISIBILITY_PUBLIC, CourseUserType.ENROLLED, False, True],

        [False, COURSE_VISIBILITY_PRIVATE, CourseUserType.UNENROLLED_STAFF, True, True],
        [True, COURSE_VISIBILITY_PRIVATE, CourseUserType.UNENROLLED_STAFF, True, True],
        [True, COURSE_VISIBILITY_PUBLIC_OUTLINE, CourseUserType.UNENROLLED_STAFF, True, True],
        [True, COURSE_VISIBILITY_PUBLIC, CourseUserType.UNENROLLED_STAFF, True, True],

        [False, COURSE_VISIBILITY_PRIVATE, CourseUserType.GLOBAL_STAFF, True, True],
        [True, COURSE_VISIBILITY_PRIVATE, CourseUserType.GLOBAL_STAFF, True, True],
        [True, COURSE_VISIBILITY_PUBLIC_OUTLINE, CourseUserType.GLOBAL_STAFF, True, True],
        [True, COURSE_VISIBILITY_PUBLIC, CourseUserType.GLOBAL_STAFF, True, True],
    )
    @ddt.unpack
    def test_home_page(
            self, enable_unenrolled_access, course_visibility, user_type,
            expected_enroll_message, expected_course_outline,
    ):
        self.create_user_for_course(self.course, user_type)

        # Render the course home page
        with mock.patch('xmodule.course_module.CourseDescriptor.course_visibility', course_visibility):
            # Test access with anonymous flag and course visibility
            with override_waffle_flag(COURSE_ENABLE_UNENROLLED_ACCESS_FLAG, enable_unenrolled_access):
                url = course_home_url(self.course)
                response = self.client.get(url)

                private_url = course_home_url(self.private_course)
                private_response = self.client.get(private_url)

        # Verify that the course tools and dates are always shown
        self.assertContains(response, TEST_COURSE_TOOLS)

        is_anonymous = user_type is CourseUserType.ANONYMOUS
        is_enrolled = user_type is CourseUserType.ENROLLED
        is_enrolled_or_staff = is_enrolled or user_type in (
            CourseUserType.UNENROLLED_STAFF, CourseUserType.GLOBAL_STAFF
        )

        self.assertContains(response, 'Learn About Verified Certificate', count=(1 if is_enrolled else 0))

        # Verify that start button, course sock, and welcome message
        # are only shown to enrolled users or staff.
        self.assertContains(response, 'Start Course', count=(1 if is_enrolled_or_staff else 0))
        self.assertContains(response, TEST_WELCOME_MESSAGE, count=(1 if is_enrolled_or_staff else 0))

        # Verify the outline is shown to enrolled users, unenrolled_staff and anonymous users if allowed
        self.assertContains(response, TEST_CHAPTER_NAME, count=(1 if expected_course_outline else 0))

        # Verify the message shown to the user
        if not enable_unenrolled_access or course_visibility != COURSE_VISIBILITY_PUBLIC:
            self.assertContains(
                response, 'To see course content', count=(1 if is_anonymous else 0)
            )
            self.assertContains(response, '<div class="user-messages"', count=(1 if expected_enroll_message else 0))
            if expected_enroll_message:
                self.assertContains(response, 'You must be enrolled in the course to see course content.')

        if enable_unenrolled_access and course_visibility == COURSE_VISIBILITY_PUBLIC:
            if user_type == CourseUserType.UNENROLLED and self.private_course.invitation_only:
                if expected_enroll_message:
                    self.assertContains(private_response,
                                        'You must be enrolled in the course to see course content.')

    @override_waffle_flag(DISABLE_UNIFIED_COURSE_TAB_FLAG, active=True)
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
        self.assertContains(response, TEST_COURSE_TOOLS)

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
        self.assertContains(response, '<div class="user-messages"', count=1 if expected_message else 0)
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

    @mock.patch('openedx.features.discounts.utils.discount_percentage')
    @mock.patch('openedx.features.discounts.utils.can_receive_discount')
    @ddt.data(
        [True, 15],
        [True, 13],
        [True, 0],
        [False, 15])
    @ddt.unpack
    def test_first_purchase_offer_banner_display(self,
                                                 applicability,
                                                 percentage,
                                                 can_receive_discount_mock,
                                                 discount_percentage_mock):
        """
        Ensure first purchase offer banner displays correctly
        """
        can_receive_discount_mock.return_value = applicability
        discount_percentage_mock.return_value = percentage
        user = self.create_user_for_course(self.course, CourseUserType.ENROLLED)
        now_time = datetime.now(tz=UTC).strftime(u"%Y-%m-%d %H:%M:%S%z")
        ExperimentData.objects.create(
            user=user, experiment_id=REV1008_EXPERIMENT_ID, key=str(self.course), value=now_time
        )
        self.client.login(username=user.username, password=self.TEST_PASSWORD)
        url = course_home_url(self.course)
        response = self.client.get(url)
        discount_expiration_date = get_discount_expiration_date(user, self.course).strftime(u'%B %d')
        upgrade_link = verified_upgrade_deadline_link(user=user, course=self.course)
        bannerText = u'''<div class="first-purchase-offer-banner" role="note">
             <span class="first-purchase-offer-banner-bold"><b>
             Upgrade by {discount_expiration_date} and save {percentage}% [{strikeout_price}]</b></span>
             <br>Use code <b>EDXWELCOME</b> at checkout! <a id="welcome" href="{upgrade_link}">Upgrade Now</a>
             </div>'''.format(
            discount_expiration_date=discount_expiration_date,
            percentage=percentage,
            strikeout_price=HTML(format_strikeout_price(user, self.course, check_for_discount=False)[0]),
            upgrade_link=upgrade_link
        )

        if applicability:
            self.assertContains(response, bannerText, html=True)
        else:
            self.assertNotContains(response, bannerText, html=True)

    @mock.patch.dict(settings.FEATURES, {'DISABLE_START_DATES': False})
    def test_course_does_not_expire_for_verified_user(self):
        """
        There are a number of different roles/users that should not lose access after the expiration date.
        Ensure that users who should not lose access get a 200 (ok) response
        when attempting to visit the course after their would be expiration date.
        """
        course = CourseFactory.create(start=THREE_YEARS_AGO)
        url = course_home_url(course)

        user = UserFactory.create(password=self.TEST_PASSWORD)
        ScheduleFactory(
            start_date=THREE_YEARS_AGO,
            enrollment__mode=CourseMode.VERIFIED,
            enrollment__course_id=course.id,
            enrollment__user=user
        )

        # ensure that the user who has indefinite access
        self.client.login(username=user.username, password=self.TEST_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            "Should not expire access for user",
        )

    @mock.patch.dict(settings.FEATURES, {'DISABLE_START_DATES': False})
    @ddt.data(
        InstructorFactory,
        StaffFactory,
        BetaTesterFactory,
        OrgStaffFactory,
        OrgInstructorFactory,
    )
    def test_course_does_not_expire_for_course_staff(self, role_factory):
        """
        There are a number of different roles/users that should not lose access after the expiration date.
        Ensure that users who should not lose access get a 200 (ok) response
        when attempting to visit the course after their would be expiration date.
        """
        course = CourseFactory.create(start=THREE_YEARS_AGO)
        url = course_home_url(course)

        user = role_factory.create(password=self.TEST_PASSWORD, course_key=course.id)
        ScheduleFactory(
            start_date=THREE_YEARS_AGO,
            enrollment__mode=CourseMode.AUDIT,
            enrollment__course_id=course.id,
            enrollment__user=user
        )

        # ensure that the user has indefinite access
        self.client.login(username=user.username, password=self.TEST_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            "Should not expire access for user",
        )

    @ddt.data(
        FORUM_ROLE_COMMUNITY_TA,
        FORUM_ROLE_GROUP_MODERATOR,
        FORUM_ROLE_MODERATOR,
        FORUM_ROLE_ADMINISTRATOR
    )
    def test_course_does_not_expire_for_user_with_course_role(self, role_name):
        """
        Test that users with the above roles for a course do not lose access
        """
        course = CourseFactory.create(start=THREE_YEARS_AGO)
        url = course_home_url(course)

        user = UserFactory.create()
        role = RoleFactory(name=role_name, course_id=course.id)
        role.users.add(user)

        # ensure the user has indefinite access
        self.client.login(username=user.username, password=self.TEST_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            "Should not expire access for user"
        )

    @mock.patch.dict(settings.FEATURES, {'DISABLE_START_DATES': False})
    @ddt.data(
        GlobalStaffFactory,
    )
    def test_course_does_not_expire_for_global_users(self, role_factory):
        """
        There are a number of different roles/users that should not lose access after the expiration date.
        Ensure that users who should not lose access get a 200 (ok) response
        when attempting to visit the course after their would be expiration date.
        """
        course = CourseFactory.create(start=THREE_YEARS_AGO)
        url = course_home_url(course)

        user = role_factory.create(password=self.TEST_PASSWORD)
        ScheduleFactory(
            start_date=THREE_YEARS_AGO,
            enrollment__mode=CourseMode.AUDIT,
            enrollment__course_id=course.id,
            enrollment__user=user
        )

        # ensure that the user who has indefinite access
        self.client.login(username=user.username, password=self.TEST_PASSWORD)
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            "Should not expire access for user",
        )

    @mock.patch.dict(settings.FEATURES, {'DISABLE_START_DATES': False})
    def test_expired_course(self):
        """
        Ensure that a user accessing an expired course sees a redirect to
        the student dashboard, not a 404.
        """
        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=datetime(2010, 1, 1, tzinfo=UTC))
        course = CourseFactory.create(start=THREE_YEARS_AGO)
        url = course_home_url(course)

        for mode in [CourseMode.AUDIT, CourseMode.VERIFIED]:
            CourseModeFactory.create(course_id=course.id, mode_slug=mode)

        # assert that an if an expired audit user tries to access the course they are redirected to the dashboard
        audit_user = UserFactory(password=self.TEST_PASSWORD)
        self.client.login(username=audit_user.username, password=self.TEST_PASSWORD)
        audit_enrollment = CourseEnrollment.enroll(audit_user, course.id, mode=CourseMode.AUDIT)
        audit_enrollment.created = THREE_YEARS_AGO + timedelta(days=1)
        audit_enrollment.save()
        ScheduleFactory(enrollment=audit_enrollment)

        response = self.client.get(url)

        expiration_date = strftime_localized(course.start + timedelta(weeks=4) + timedelta(days=1), u'%b %-d, %Y')
        expected_params = QueryDict(mutable=True)
        course_name = CourseOverview.get_from_id(course.id).display_name_with_default
        expected_params['access_response_error'] = u'Access to {run} expired on {expiration_date}'.format(
            run=course_name,
            expiration_date=expiration_date
        )
        expected_url = '{url}?{params}'.format(
            url=reverse('dashboard'),
            params=expected_params.urlencode()
        )
        self.assertRedirects(response, expected_url)

    @mock.patch.dict(settings.FEATURES, {'DISABLE_START_DATES': False})
    def test_expiration_banner_with_expired_upgrade_deadline(self):
        """
        Ensure that a user accessing a course with an expired upgrade deadline
        will still see the course expiration banner without the upgrade related text.
        """
        past = datetime(2010, 1, 1, tzinfo=UTC)
        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=past)
        course = CourseFactory.create(start=now() - timedelta(days=10))
        CourseModeFactory.create(course_id=course.id, mode_slug=CourseMode.AUDIT)
        CourseModeFactory.create(course_id=course.id, mode_slug=CourseMode.VERIFIED, expiration_datetime=past)
        user = UserFactory(password=self.TEST_PASSWORD)
        self.client.login(username=user.username, password=self.TEST_PASSWORD)
        CourseEnrollment.enroll(user, course.id, mode=CourseMode.AUDIT)

        url = course_home_url(course)
        response = self.client.get(url)
        bannerText = get_expiration_banner_text(user, course)
        self.assertContains(response, bannerText, html=True)
        self.assertContains(response, TEST_BANNER_CLASS)

    def test_audit_only_not_expired(self):
        """
        Verify that enrolled users are NOT shown the course expiration banner and can
        access the course home page if course audit only
        """
        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=datetime(2010, 1, 1, tzinfo=UTC))
        audit_only_course = CourseFactory.create()
        self.create_user_for_course(audit_only_course, CourseUserType.ENROLLED)
        response = self.client.get(course_home_url(audit_only_course))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, TEST_COURSE_TOOLS)
        self.assertNotContains(response, TEST_BANNER_CLASS)

    @mock.patch.dict(settings.FEATURES, {'DISABLE_START_DATES': False})
    def test_expired_course_in_holdback(self):
        """
        Ensure that a user accessing an expired course that is in the holdback
        does not get redirected to the student dashboard, not a 404.
        """
        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=datetime(2010, 1, 1, tzinfo=UTC))

        course = CourseFactory.create(start=THREE_YEARS_AGO)
        url = course_home_url(course)

        for mode in [CourseMode.AUDIT, CourseMode.VERIFIED]:
            CourseModeFactory.create(course_id=course.id, mode_slug=mode)

        # assert that an if an expired audit user in the holdback tries to access the course
        # they are not redirected to the dashboard
        audit_user = UserFactory(password=self.TEST_PASSWORD)
        self.client.login(username=audit_user.username, password=self.TEST_PASSWORD)
        audit_enrollment = CourseEnrollment.enroll(audit_user, course.id, mode=CourseMode.AUDIT)
        ScheduleFactory(start_date=THREE_YEARS_AGO, enrollment=audit_enrollment)
        FBEEnrollmentExclusion.objects.create(
            enrollment=audit_enrollment
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    @mock.patch.dict(settings.FEATURES, {'DISABLE_START_DATES': False})
    @mock.patch("common.djangoapps.util.date_utils.strftime_localized")
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
    def test_masters_course_message(self):
        enroll_button_html = "<button class=\"enroll-btn btn-link\">Enroll now</button>"

        # Verify that unenrolled users visiting a course with a Master's track
        # that is not the only track are shown an enroll call to action message
        add_course_mode(self.course, CourseMode.MASTERS, 'Master\'s Mode', upgrade_deadline_expired=False)
        remove_course_mode(self.course, CourseMode.AUDIT)

        self.create_user_for_course(self.course, CourseUserType.UNENROLLED)
        url = course_home_url(self.course)
        response = self.client.get(url)

        self.assertContains(response, TEST_COURSE_HOME_MESSAGE)
        self.assertContains(response, TEST_COURSE_HOME_MESSAGE_UNENROLLED)
        self.assertContains(response, enroll_button_html)

        # Verify that unenrolled users visiting a course that contains only a Master's track
        # are not shown an enroll call to action message
        remove_course_mode(self.course, CourseMode.VERIFIED)

        response = self.client.get(url)

        expected_message = ('You must be enrolled in the course to see course content. '
                            'Please contact your degree administrator or edX Support if you have questions.')
        self.assertContains(response, TEST_COURSE_HOME_MESSAGE)
        self.assertContains(response, expected_message)
        self.assertNotContains(response, enroll_button_html)

    @override_waffle_flag(COURSE_PRE_START_ACCESS_FLAG, active=True)
    def test_course_messaging(self):
        """
        Ensure that the following four use cases work as expected

        1) Anonymous users are shown a course message linking them to the login page
        2) Unenrolled users are shown a course message allowing them to enroll
        3) Enrolled users who show up on the course page after the course has begun
        are not shown a course message.
        4) Enrolled users who show up on the course page after the course has begun will
        see the course expiration banner if course duration limits are on for the course.
        5) Enrolled users who show up on the course page before the course begins
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

        # Verify that enrolled users are shown the course expiration banner if content gating is enabled

        # We use .save() explicitly here (rather than .objects.create) in order to force the
        # cache to refresh.
        config = CourseDurationLimitConfig(
            course=CourseOverview.get_from_id(self.course.id),
            enabled=True,
            enabled_as_of=datetime(2018, 1, 1, tzinfo=UTC)
        )
        config.save()

        url = course_home_url(self.course)
        response = self.client.get(url)
        bannerText = get_expiration_banner_text(user, self.course)
        self.assertContains(response, bannerText, html=True)

        # Verify that enrolled users are not shown the course expiration banner if content gating is disabled
        config.enabled = False
        config.save()
        url = course_home_url(self.course)
        response = self.client.get(url)
        bannerText = get_expiration_banner_text(user, self.course)
        self.assertNotContains(response, bannerText, html=True)

        # Verify that enrolled users are shown 'days until start' message before start date
        future_course = self.create_future_course()
        CourseEnrollment.enroll(user, future_course.id)
        url = course_home_url(future_course)
        response = self.client.get(url)
        self.assertContains(response, TEST_COURSE_HOME_MESSAGE)
        self.assertContains(response, TEST_COURSE_HOME_MESSAGE_PRE_START)

    def test_course_messaging_for_staff(self):
        """
        Staff users will not see the expiration banner when course duration limits
        are on for the course.
        """
        config = CourseDurationLimitConfig(
            course=CourseOverview.get_from_id(self.course.id),
            enabled=True,
            enabled_as_of=datetime(2018, 1, 1, tzinfo=UTC)
        )
        config.save()
        url = course_home_url(self.course)
        CourseEnrollment.enroll(self.staff_user, self.course.id)
        response = self.client.get(url)
        bannerText = get_expiration_banner_text(self.staff_user, self.course)
        self.assertNotContains(response, bannerText, html=True)

    @mock.patch("common.djangoapps.util.date_utils.strftime_localized")
    @mock.patch("openedx.features.course_duration_limits.access.get_date_string")
    def test_course_expiration_banner_with_unicode(self, mock_strftime_localized, mock_get_date_string):
        """
        Ensure that switching to other languages that have unicode in their
        date representations will not cause the course home page to 404.
        """
        fake_unicode_start_time = u"üñîçø∂é_ßtå®t_tîµé"
        mock_strftime_localized.return_value = fake_unicode_start_time
        date_string = u'<span class="localized-datetime" data-format="shortDate" \
        data-datetime="{formatted_date}" data-language="{language}">{formatted_date_localized}</span>'
        mock_get_date_string.return_value = date_string

        config = CourseDurationLimitConfig(
            course=CourseOverview.get_from_id(self.course.id),
            enabled=True,
            enabled_as_of=datetime(2018, 1, 1, tzinfo=UTC)
        )
        config.save()
        url = course_home_url(self.course)
        user = self.create_user_for_course(self.course, CourseUserType.UNENROLLED)
        CourseEnrollment.enroll(user, self.course.id)

        language = 'eo'
        DarkLangConfig(
            released_languages=language,
            changed_by=user,
            enabled=True
        ).save()

        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE=language)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Language'], language)

        # Check that if the string is incorrectly not marked as unicode we still get the error
        with mock.patch("openedx.features.course_duration_limits.access.get_date_string",
                        return_value=date_string.encode('utf-8')):
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE=language)
            self.assertEqual(response.status_code, 500)

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


@ddt.ddt
class CourseHomeFragmentViewTests(ModuleStoreTestCase):
    """
    Test Messages Displayed on the Course Home
    """
    CREATE_USER = False

    def setUp(self):
        super(CourseHomeFragmentViewTests, self).setUp()
        CommerceConfiguration.objects.create(checkout_on_ecommerce_service=True)

        end = now() + timedelta(days=30)
        self.course = CourseFactory(
            start=now() - timedelta(days=30),
            end=end,
            self_paced=True,
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
        self.assertNotContains(response, 'section-upgrade')

    def assert_upgrade_message_displayed(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'section-upgrade')
        url = EcommerceService().get_checkout_page_url(self.verified_mode.sku)
        self.assertContains(response, '<a id="green_upgrade" class="btn-brand btn-upgrade"')
        self.assertContains(response, url)
        self.assertContains(
            response,
            u"Upgrade (<span class='price'>${price}</span>)".format(price=self.verified_mode.min_price),
        )

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

    @mock.patch(
        'openedx.features.course_experience.views.course_home.format_strikeout_price',
        mock.Mock(return_value=(HTML("<span>DISCOUNT_PRICE</span>"), True))
    )
    def test_upgrade_message_discount(self):
        # pylint: disable=no-member
        CourseEnrollment.enroll(self.user, self.course.id, CourseMode.AUDIT)

        with override_waffle_flag(SHOW_UPGRADE_MSG_ON_COURSE_HOME, True):
            response = self.client.get(self.url)

        self.assertContains(response, "<span>DISCOUNT_PRICE</span>")
