# -*- coding: utf-8 -*-
"""
Test the access control framework
"""
import datetime
import ddt
import itertools
import pytz

from django.contrib.auth.models import User
from ccx_keys.locator import CCXLocator
from django.http import Http404
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import Mock, patch
from nose.plugins.attrib import attr
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from ccx.tests.factories import CcxFactory
import courseware.access as access
import courseware.access_response as access_response
from courseware.masquerade import CourseMasquerade
from courseware.tests.factories import (
    BetaTesterFactory,
    GlobalStaffFactory,
    InstructorFactory,
    StaffFactory,
    UserFactory,
)
import courseware.views.views as views
from courseware.tests.helpers import LoginEnrollmentTestCase
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment
from student.roles import CourseCcxCoachRole
from student.tests.factories import (
    AdminFactory,
    AnonymousUserFactory,
    CourseEnrollmentAllowedFactory,
    CourseEnrollmentFactory,
)

from xmodule.course_module import (
    CATALOG_VISIBILITY_CATALOG_AND_ABOUT,
    CATALOG_VISIBILITY_ABOUT,
    CATALOG_VISIBILITY_NONE,
)
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    SharedModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE
)
from xmodule.modulestore.xml import CourseLocationManager
from xmodule.tests import get_test_system

from util.milestones_helpers import (
    set_prerequisite_courses,
    fulfill_course_milestone,
)
from milestones.tests.utils import MilestonesTestCaseMixin

from lms.djangoapps.ccx.models import CustomCourseForEdX

# pylint: disable=protected-access


class CoachAccessTestCaseCCX(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test if user is coach on ccx.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        """
        Set up course for tests
        """
        super(CoachAccessTestCaseCCX, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        """
        Set up tests
        """
        super(CoachAccessTestCaseCCX, self).setUp()

        # Create ccx coach account
        self.coach = AdminFactory.create(password="test")
        self.client.login(username=self.coach.username, password="test")

        # assign role to coach
        role = CourseCcxCoachRole(self.course.id)
        role.add_users(self.coach)
        self.request_factory = RequestFactory()

    def make_ccx(self):
        """
        create ccx
        """
        ccx = CustomCourseForEdX(
            course_id=self.course.id,
            coach=self.coach,
            display_name="Test CCX"
        )
        ccx.save()

        ccx_locator = CCXLocator.from_course_locator(self.course.id, unicode(ccx.id))
        role = CourseCcxCoachRole(ccx_locator)
        role.add_users(self.coach)
        CourseEnrollment.enroll(self.coach, ccx_locator)
        return ccx_locator

    def test_has_ccx_coach_role(self):
        """
        Assert that user has coach access on ccx.
        """
        ccx_locator = self.make_ccx()

        # user have access as coach on ccx
        self.assertTrue(access.has_ccx_coach_role(self.coach, ccx_locator))

        # user dont have access as coach on ccx
        self.setup_user()
        self.assertFalse(access.has_ccx_coach_role(self.user, ccx_locator))

    def test_access_student_progress_ccx(self):
        """
        Assert that only a coach can see progress of student.
        """
        ccx_locator = self.make_ccx()
        student = UserFactory()

        # Enroll user
        CourseEnrollment.enroll(student, ccx_locator)

        # Test for access of a coach
        resp = self.client.get(reverse('student_progress', args=[unicode(ccx_locator), student.id]))
        self.assertEqual(resp.status_code, 200)

        # Assert access of a student
        self.client.login(username=student.username, password='test')
        resp = self.client.get(reverse('student_progress', args=[unicode(ccx_locator), self.coach.id]))
        self.assertEqual(resp.status_code, 404)


@attr('shard_1')
@ddt.ddt
class AccessTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase, MilestonesTestCaseMixin):
    """
    Tests for the various access controls on the student dashboard
    """
    TOMORROW = datetime.datetime.now(pytz.utc) + datetime.timedelta(days=1)
    YESTERDAY = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=1)
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super(AccessTestCase, self).setUp()
        self.course = CourseFactory.create(org='edX', course='toy', run='test_run')
        self.anonymous_user = AnonymousUserFactory()
        self.beta_user = BetaTesterFactory(course_key=self.course.id)
        self.student = UserFactory()
        self.global_staff = UserFactory(is_staff=True)
        self.course_staff = StaffFactory(course_key=self.course.id)
        self.course_instructor = InstructorFactory(course_key=self.course.id)
        self.staff = GlobalStaffFactory()

    def verify_access(self, mock_unit, student_should_have_access, expected_error_type=None):
        """ Verify the expected result from _has_access_descriptor """
        response = access._has_access_descriptor(self.anonymous_user, 'load',
                                                 mock_unit, course_key=self.course.id)
        self.assertEqual(student_should_have_access, bool(response))

        if expected_error_type is not None:
            self.assertIsInstance(response, expected_error_type)
            self.assertIsNotNone(response.to_json()['error_code'])

        self.assertTrue(
            access._has_access_descriptor(self.course_staff, 'load', mock_unit, course_key=self.course.id)
        )

    def test_has_staff_access_to_preview_mode(self):
        """
        Tests users have right access to content in preview mode.
        """
        course_key = self.course.id
        usage_key = self.course.scope_ids.usage_id
        chapter = ItemFactory.create(category="chapter", parent_location=self.course.location)
        overview = CourseOverview.get_from_id(course_key)
        test_system = get_test_system()

        ccx = CcxFactory(course_id=course_key)
        ccx_locator = CCXLocator.from_course_locator(course_key, ccx.id)

        error_descriptor = ErrorDescriptor.from_xml(
            u"<problem>ABC \N{SNOWMAN}</problem>",
            test_system,
            CourseLocationManager(course_key),
            "error msg"
        )
        # Enroll student to the course
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

        modules = [
            self.course,
            overview,
            chapter,
            ccx_locator,
            error_descriptor,
            course_key,
            usage_key,
        ]
        # Course key is not None
        self.assertTrue(
            bool(access.has_staff_access_to_preview_mode(self.global_staff, obj=self.course, course_key=course_key))
        )

        for user in [self.global_staff, self.course_staff, self.course_instructor]:
            for obj in modules:
                self.assertTrue(bool(access.has_staff_access_to_preview_mode(user, obj=obj)))
                self.assertFalse(bool(access.has_staff_access_to_preview_mode(self.student, obj=obj)))

    def test_student_has_access(self):
        """
        Tests course student have right access to content w/o preview.
        """
        course_key = self.course.id
        chapter = ItemFactory.create(category="chapter", parent_location=self.course.location)
        overview = CourseOverview.get_from_id(course_key)

        # Enroll student to the course
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

        modules = [
            self.course,
            overview,
            chapter,
        ]
        with patch('courseware.access.in_preview_mode') as mock_preview:
            mock_preview.return_value = False
            for obj in modules:
                self.assertTrue(bool(access.has_access(self.student, 'load', obj, course_key=self.course.id)))

        with patch('courseware.access.in_preview_mode') as mock_preview:
            mock_preview.return_value = True
            for obj in modules:
                self.assertFalse(bool(access.has_access(self.student, 'load', obj, course_key=self.course.id)))

    def test_string_has_staff_access_to_preview_mode(self):
        """
        Tests different users has right access to string content in preview mode.
        """
        self.assertTrue(bool(access.has_staff_access_to_preview_mode(self.global_staff, obj='global')))
        self.assertFalse(bool(access.has_staff_access_to_preview_mode(self.course_staff, obj='global')))
        self.assertFalse(bool(access.has_staff_access_to_preview_mode(self.course_instructor, obj='global')))
        self.assertFalse(bool(access.has_staff_access_to_preview_mode(self.student, obj='global')))

    @patch('courseware.access.in_preview_mode', Mock(return_value=True))
    def test_has_access_with_preview_mode(self):
        """
        Tests particular user's can access content via has_access in preview mode.
        """
        self.assertTrue(bool(access.has_access(self.global_staff, 'staff', self.course, course_key=self.course.id)))
        self.assertTrue(bool(access.has_access(self.course_staff, 'staff', self.course, course_key=self.course.id)))
        self.assertTrue(bool(access.has_access(
            self.course_instructor, 'staff', self.course, course_key=self.course.id
        )))
        self.assertFalse(bool(access.has_access(self.student, 'staff', self.course, course_key=self.course.id)))
        self.assertFalse(bool(access.has_access(self.student, 'load', self.course, course_key=self.course.id)))

        # User should be able to preview when masquerade.
        with patch('courseware.access.is_masquerading_as_student') as mock_masquerade:
            mock_masquerade.return_value = True
            self.assertTrue(
                bool(access.has_access(self.global_staff, 'staff', self.course, course_key=self.course.id))
            )
            self.assertFalse(
                bool(access.has_access(self.student, 'staff', self.course, course_key=self.course.id))
            )

    def test_has_access_to_course(self):
        self.assertFalse(access._has_access_to_course(
            None, 'staff', self.course.id
        ))

        self.assertFalse(access._has_access_to_course(
            self.anonymous_user, 'staff', self.course.id
        ))
        self.assertFalse(access._has_access_to_course(
            self.anonymous_user, 'instructor', self.course.id
        ))

        self.assertTrue(access._has_access_to_course(
            self.global_staff, 'staff', self.course.id
        ))
        self.assertTrue(access._has_access_to_course(
            self.global_staff, 'instructor', self.course.id
        ))

        # A user has staff access if they are in the staff group
        self.assertTrue(access._has_access_to_course(
            self.course_staff, 'staff', self.course.id
        ))
        self.assertFalse(access._has_access_to_course(
            self.course_staff, 'instructor', self.course.id
        ))

        # A user has staff and instructor access if they are in the instructor group
        self.assertTrue(access._has_access_to_course(
            self.course_instructor, 'staff', self.course.id
        ))
        self.assertTrue(access._has_access_to_course(
            self.course_instructor, 'instructor', self.course.id
        ))

        # A user does not have staff or instructor access if they are
        # not in either the staff or the the instructor group
        self.assertFalse(access._has_access_to_course(
            self.student, 'staff', self.course.id
        ))
        self.assertFalse(access._has_access_to_course(
            self.student, 'instructor', self.course.id
        ))

        self.assertFalse(access._has_access_to_course(
            self.student, 'not_staff_or_instructor', self.course.id
        ))

    def test__has_access_string(self):
        user = Mock(is_staff=True)
        self.assertFalse(access._has_access_string(user, 'staff', 'not_global'))

        user._has_global_staff_access.return_value = True
        self.assertTrue(access._has_access_string(user, 'staff', 'global'))

        self.assertRaises(ValueError, access._has_access_string, user, 'not_staff', 'global')

    @ddt.data(
        ('load', False, True, True),
        ('staff', False, True, True),
        ('instructor', False, False, True)
    )
    @ddt.unpack
    def test__has_access_error_desc(self, action, expected_student, expected_staff, expected_instructor):
        descriptor = Mock()

        for (user, expected_response) in (
                (self.student, expected_student),
                (self.course_staff, expected_staff),
                (self.course_instructor, expected_instructor)
        ):
            self.assertEquals(
                bool(access._has_access_error_desc(user, action, descriptor, self.course.id)),
                expected_response
            )

        with self.assertRaises(ValueError):
            access._has_access_error_desc(self.course_instructor, 'not_load_or_staff', descriptor, self.course.id)

    def test__has_access_descriptor(self):
        # TODO: override DISABLE_START_DATES and test the start date branch of the method
        user = Mock()
        descriptor = Mock(user_partitions=[])
        descriptor._class_tags = {}

        # Always returns true because DISABLE_START_DATES is set in test.py
        self.assertTrue(access._has_access_descriptor(user, 'load', descriptor))
        self.assertTrue(access._has_access_descriptor(user, 'instructor', descriptor))
        with self.assertRaises(ValueError):
            access._has_access_descriptor(user, 'not_load_or_staff', descriptor)

    @ddt.data(
        (True, None, access_response.VisibilityError),
        (False, None),
        (True, YESTERDAY, access_response.VisibilityError),
        (False, YESTERDAY),
        (True, TOMORROW, access_response.VisibilityError),
        (False, TOMORROW, access_response.StartDateError)
    )
    @ddt.unpack
    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test__has_access_descriptor_staff_lock(self, visible_to_staff_only, start, expected_error_type=None):
        """
        Tests that "visible_to_staff_only" overrides start date.
        """
        expected_access = expected_error_type is None
        mock_unit = Mock(user_partitions=[])
        mock_unit._class_tags = {}  # Needed for detached check in _has_access_descriptor
        mock_unit.visible_to_staff_only = visible_to_staff_only
        mock_unit.start = start
        self.verify_access(mock_unit, expected_access, expected_error_type)

    def test__has_access_descriptor_beta_user(self):
        mock_unit = Mock(user_partitions=[])
        mock_unit._class_tags = {}
        mock_unit.days_early_for_beta = 2
        mock_unit.start = self.TOMORROW
        mock_unit.visible_to_staff_only = False

        self.assertTrue(bool(access._has_access_descriptor(
            self.beta_user, 'load', mock_unit, course_key=self.course.id)))

    @ddt.data(None, YESTERDAY, TOMORROW)
    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    @patch('courseware.access_utils.get_current_request_hostname', Mock(return_value='preview.localhost'))
    def test__has_access_descriptor_in_preview_mode(self, start):
        """
        Tests that descriptor has access in preview mode.
        """
        mock_unit = Mock(user_partitions=[])
        mock_unit._class_tags = {}  # Needed for detached check in _has_access_descriptor
        mock_unit.visible_to_staff_only = False
        mock_unit.start = start
        self.verify_access(mock_unit, True)

    @ddt.data(
        (TOMORROW, access_response.StartDateError),
        (None, None),
        (YESTERDAY, None)
    )  # ddt throws an error if I don't put the None argument there
    @ddt.unpack
    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    @patch('courseware.access_utils.get_current_request_hostname', Mock(return_value='localhost'))
    def test__has_access_descriptor_when_not_in_preview_mode(self, start, expected_error_type):
        """
        Tests that descriptor has no access when start date in future & without preview.
        """
        expected_access = expected_error_type is None
        mock_unit = Mock(user_partitions=[])
        mock_unit._class_tags = {}  # Needed for detached check in _has_access_descriptor
        mock_unit.visible_to_staff_only = False
        mock_unit.start = start
        self.verify_access(mock_unit, expected_access, expected_error_type)

    def test__has_access_course_can_enroll(self):
        yesterday = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=1)
        tomorrow = datetime.datetime.now(pytz.utc) + datetime.timedelta(days=1)

        # Non-staff can enroll if authenticated and specifically allowed for that course
        # even outside the open enrollment period
        user = UserFactory.create()
        course = Mock(
            enrollment_start=tomorrow, enrollment_end=tomorrow,
            id=SlashSeparatedCourseKey('edX', 'test', '2012_Fall'), enrollment_domain=''
        )
        CourseEnrollmentAllowedFactory(email=user.email, course_id=course.id)
        self.assertTrue(access._has_access_course(user, 'enroll', course))

        # Staff can always enroll even outside the open enrollment period
        user = StaffFactory.create(course_key=course.id)
        self.assertTrue(access._has_access_course(user, 'enroll', course))

        # Non-staff cannot enroll if it is between the start and end dates and invitation only
        # and not specifically allowed
        course = Mock(
            enrollment_start=yesterday, enrollment_end=tomorrow,
            id=SlashSeparatedCourseKey('edX', 'test', '2012_Fall'), enrollment_domain='',
            invitation_only=True
        )
        user = UserFactory.create()
        self.assertFalse(access._has_access_course(user, 'enroll', course))

        # Non-staff can enroll if it is between the start and end dates and not invitation only
        course = Mock(
            enrollment_start=yesterday, enrollment_end=tomorrow,
            id=SlashSeparatedCourseKey('edX', 'test', '2012_Fall'), enrollment_domain='',
            invitation_only=False
        )
        self.assertTrue(access._has_access_course(user, 'enroll', course))

        # Non-staff cannot enroll outside the open enrollment period if not specifically allowed
        course = Mock(
            enrollment_start=tomorrow, enrollment_end=tomorrow,
            id=SlashSeparatedCourseKey('edX', 'test', '2012_Fall'), enrollment_domain='',
            invitation_only=False
        )
        self.assertFalse(access._has_access_course(user, 'enroll', course))

    def test__user_passed_as_none(self):
        """Ensure has_access handles a user being passed as null"""
        access.has_access(None, 'staff', 'global', None)

    def test__catalog_visibility(self):
        """
        Tests the catalog visibility tri-states
        """
        user = UserFactory.create()
        course_id = SlashSeparatedCourseKey('edX', 'test', '2012_Fall')
        staff = StaffFactory.create(course_key=course_id)

        course = Mock(
            id=course_id,
            catalog_visibility=CATALOG_VISIBILITY_CATALOG_AND_ABOUT
        )
        self.assertTrue(access._has_access_course(user, 'see_in_catalog', course))
        self.assertTrue(access._has_access_course(user, 'see_about_page', course))
        self.assertTrue(access._has_access_course(staff, 'see_in_catalog', course))
        self.assertTrue(access._has_access_course(staff, 'see_about_page', course))

        # Now set visibility to just about page
        course = Mock(
            id=SlashSeparatedCourseKey('edX', 'test', '2012_Fall'),
            catalog_visibility=CATALOG_VISIBILITY_ABOUT
        )
        self.assertFalse(access._has_access_course(user, 'see_in_catalog', course))
        self.assertTrue(access._has_access_course(user, 'see_about_page', course))
        self.assertTrue(access._has_access_course(staff, 'see_in_catalog', course))
        self.assertTrue(access._has_access_course(staff, 'see_about_page', course))

        # Now set visibility to none, which means neither in catalog nor about pages
        course = Mock(
            id=SlashSeparatedCourseKey('edX', 'test', '2012_Fall'),
            catalog_visibility=CATALOG_VISIBILITY_NONE
        )
        self.assertFalse(access._has_access_course(user, 'see_in_catalog', course))
        self.assertFalse(access._has_access_course(user, 'see_about_page', course))
        self.assertTrue(access._has_access_course(staff, 'see_in_catalog', course))
        self.assertTrue(access._has_access_course(staff, 'see_about_page', course))

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_PREREQUISITE_COURSES': True, 'MILESTONES_APP': True})
    def test_access_on_course_with_pre_requisites(self):
        """
        Test course access when a course has pre-requisite course yet to be completed
        """
        user = UserFactory.create()

        pre_requisite_course = CourseFactory.create(
            org='test_org', number='788', run='test_run'
        )

        pre_requisite_courses = [unicode(pre_requisite_course.id)]
        course = CourseFactory.create(
            org='test_org', number='786', run='test_run', pre_requisite_courses=pre_requisite_courses
        )
        set_prerequisite_courses(course.id, pre_requisite_courses)

        # user should not be able to load course even if enrolled
        CourseEnrollmentFactory(user=user, course_id=course.id)
        response = access._has_access_course(user, 'view_courseware_with_prerequisites', course)
        self.assertFalse(response)
        self.assertIsInstance(response, access_response.MilestoneError)
        # Staff can always access course
        staff = StaffFactory.create(course_key=course.id)
        self.assertTrue(access._has_access_course(staff, 'view_courseware_with_prerequisites', course))

        # User should be able access after completing required course
        fulfill_course_milestone(pre_requisite_course.id, user)
        self.assertTrue(access._has_access_course(user, 'view_courseware_with_prerequisites', course))

    @ddt.data(
        (True, True, True),
        (False, False, True)
    )
    @ddt.unpack
    def test__access_on_mobile(self, mobile_available, student_expected, staff_expected):
        """
        Test course access on mobile for staff and students.
        """
        descriptor = Mock(user_partitions=[])
        descriptor._class_tags = {}
        descriptor.visible_to_staff_only = False
        descriptor.mobile_available = mobile_available

        self.assertEqual(
            bool(access._has_access_course(self.student, 'load_mobile', descriptor)),
            student_expected
        )
        self.assertEqual(bool(access._has_access_course(self.staff, 'load_mobile', descriptor)), staff_expected)

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_PREREQUISITE_COURSES': True, 'MILESTONES_APP': True})
    def test_courseware_page_unfulfilled_prereqs(self):
        """
        Test courseware access when a course has pre-requisite course yet to be completed
        """
        pre_requisite_course = CourseFactory.create(
            org='edX',
            course='900',
            run='test_run',
        )

        pre_requisite_courses = [unicode(pre_requisite_course.id)]
        course = CourseFactory.create(
            org='edX',
            course='1000',
            run='test_run',
            pre_requisite_courses=pre_requisite_courses,
        )
        set_prerequisite_courses(course.id, pre_requisite_courses)

        test_password = 't3stp4ss.!'
        user = UserFactory.create()
        user.set_password(test_password)
        user.save()
        self.login(user.email, test_password)
        CourseEnrollmentFactory(user=user, course_id=course.id)

        url = reverse('courseware', args=[unicode(course.id)])
        response = self.client.get(url)
        self.assertRedirects(
            response,
            reverse(
                'dashboard'
            )
        )
        self.assertEqual(response.status_code, 302)

        fulfill_course_milestone(pre_requisite_course.id, user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


@attr('shard_1')
class UserRoleTestCase(TestCase):
    """
    Tests for user roles.
    """

    def setUp(self):
        super(UserRoleTestCase, self).setUp()
        self.course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')
        self.anonymous_user = AnonymousUserFactory()
        self.student = UserFactory()
        self.global_staff = UserFactory(is_staff=True)
        self.course_staff = StaffFactory(course_key=self.course_key)
        self.course_instructor = InstructorFactory(course_key=self.course_key)

    def _install_masquerade(self, user, role='student'):
        """
        Installs a masquerade for the specified user.
        """
        user.masquerade_settings = {
            self.course_key: CourseMasquerade(self.course_key, role=role)
        }

    def test_user_role_staff(self):
        """Ensure that user role is student for staff masqueraded as student."""
        self.assertEqual(
            'staff',
            access.get_user_role(self.course_staff, self.course_key)
        )
        # Masquerade staff
        self._install_masquerade(self.course_staff)
        self.assertEqual(
            'student',
            access.get_user_role(self.course_staff, self.course_key)
        )

    def test_user_role_instructor(self):
        """Ensure that user role is student for instructor masqueraded as student."""
        self.assertEqual(
            'instructor',
            access.get_user_role(self.course_instructor, self.course_key)
        )
        # Masquerade instructor
        self._install_masquerade(self.course_instructor)
        self.assertEqual(
            'student',
            access.get_user_role(self.course_instructor, self.course_key)
        )

    def test_user_role_anonymous(self):
        """Ensure that user role is student for anonymous user."""
        self.assertEqual(
            'student',
            access.get_user_role(self.anonymous_user, self.course_key)
        )


@attr('shard_3')
@ddt.ddt
class CourseOverviewAccessTestCase(ModuleStoreTestCase):
    """
    Tests confirming that has_access works equally on CourseDescriptors and
    CourseOverviews.
    """

    def setUp(self):
        super(CourseOverviewAccessTestCase, self).setUp()

        today = datetime.datetime.now(pytz.UTC)
        last_week = today - datetime.timedelta(days=7)
        next_week = today + datetime.timedelta(days=7)

        self.course_default = CourseFactory.create()
        self.course_started = CourseFactory.create(start=last_week)
        self.course_not_started = CourseFactory.create(start=next_week, days_early_for_beta=10)
        self.course_staff_only = CourseFactory.create(visible_to_staff_only=True)
        self.course_mobile_available = CourseFactory.create(mobile_available=True)
        self.course_with_pre_requisite = CourseFactory.create(
            pre_requisite_courses=[str(self.course_started.id)]
        )
        self.course_with_pre_requisites = CourseFactory.create(
            pre_requisite_courses=[str(self.course_started.id), str(self.course_not_started.id)]
        )

        self.user_normal = UserFactory.create()
        self.user_beta_tester = BetaTesterFactory.create(course_key=self.course_not_started.id)
        self.user_completed_pre_requisite = UserFactory.create()
        fulfill_course_milestone(self.user_completed_pre_requisite, self.course_started.id)
        self.user_staff = UserFactory.create(is_staff=True)
        self.user_anonymous = AnonymousUserFactory.create()

    COURSE_TEST_DATA = list(itertools.product(
        ['user_normal', 'user_staff', 'user_anonymous'],
        ['enroll', 'load', 'staff', 'instructor', 'see_exists', 'see_in_catalog', 'see_about_page'],
        ['course_default', 'course_started', 'course_not_started', 'course_staff_only'],
    ))

    LOAD_MOBILE_TEST_DATA = list(itertools.product(
        ['user_normal', 'user_staff'],
        ['load_mobile'],
        ['course_default', 'course_mobile_available'],
    ))

    PREREQUISITES_TEST_DATA = list(itertools.product(
        ['user_normal', 'user_completed_pre_requisite', 'user_staff', 'user_anonymous'],
        ['view_courseware_with_prerequisites'],
        ['course_default', 'course_with_pre_requisite', 'course_with_pre_requisites'],
    ))

    @ddt.data(*(COURSE_TEST_DATA + LOAD_MOBILE_TEST_DATA + PREREQUISITES_TEST_DATA))
    @ddt.unpack
    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_course_overview_access(self, user_attr_name, action, course_attr_name):
        """
        Check that a user's access to a course is equal to the user's access to
        the corresponding course overview.

        Instead of taking a user and course directly as arguments, we have to
        take their attribute names, as ddt doesn't allow us to reference self.

        Arguments:
            user_attr_name (str): the name of the attribute on self that is the
                User to test with.
            action (str): action to test with.
            course_attr_name (str): the name of the attribute on self that is
                the CourseDescriptor to test with.
        """
        user = getattr(self, user_attr_name)
        course = getattr(self, course_attr_name)

        course_overview = CourseOverview.get_from_id(course.id)
        self.assertEqual(
            bool(access.has_access(user, action, course, course_key=course.id)),
            bool(access.has_access(user, action, course_overview, course_key=course.id))
        )

    def test_course_overview_unsupported_action(self):
        """
        Check that calling has_access with an unsupported action raises a
        ValueError.
        """
        overview = CourseOverview.get_from_id(self.course_default.id)
        with self.assertRaises(ValueError):
            access.has_access(self.user, '_non_existent_action', overview)

    @ddt.data(
        *itertools.product(
            ['user_normal', 'user_staff', 'user_anonymous'],
            ['see_exists', 'see_in_catalog', 'see_about_page'],
            ['course_default', 'course_started', 'course_not_started'],
        )
    )
    @ddt.unpack
    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_course_catalog_access_num_queries(self, user_attr_name, action, course_attr_name):
        course = getattr(self, course_attr_name)

        # get a fresh user object that won't have any cached role information
        if user_attr_name == 'user_anonymous':
            user = AnonymousUserFactory()
        else:
            user = getattr(self, user_attr_name)
            user = User.objects.get(id=user.id)

        if user_attr_name == 'user_staff' and action == 'see_exists' and course_attr_name == 'course_not_started':
            # checks staff role
            num_queries = 1
        elif user_attr_name == 'user_normal' and action == 'see_exists' and course_attr_name != 'course_started':
            # checks staff role and enrollment data
            num_queries = 2
        else:
            num_queries = 0

        course_overview = CourseOverview.get_from_id(course.id)
        with self.assertNumQueries(num_queries):
            bool(access.has_access(user, action, course_overview, course_key=course.id))
