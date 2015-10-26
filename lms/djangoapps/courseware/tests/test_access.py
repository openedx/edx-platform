# -*- coding: utf-8 -*-
"""
Test the access control framework
"""
import datetime
import ddt
import itertools
import pytz

from django.test import TestCase
from django.core.urlresolvers import reverse
from mock import Mock, patch
from nose.plugins.attrib import attr
from opaque_keys.edx.locations import SlashSeparatedCourseKey

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
from courseware.tests.helpers import LoginEnrollmentTestCase
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.tests.factories import (
    AnonymousUserFactory,
    CourseEnrollmentAllowedFactory,
    CourseEnrollmentFactory,
)
from xmodule.course_module import (
    CATALOG_VISIBILITY_CATALOG_AND_ABOUT,
    CATALOG_VISIBILITY_ABOUT,
    CATALOG_VISIBILITY_NONE,
)
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from util.milestones_helpers import (
    set_prerequisite_courses,
    fulfill_course_milestone,
    seed_milestone_relationship_types,
)

# pylint: disable=missing-docstring
# pylint: disable=protected-access


@attr('shard_1')
@ddt.ddt
class AccessTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Tests for the various access controls on the student dashboard
    """
    TOMORROW = datetime.datetime.now(pytz.utc) + datetime.timedelta(days=1)
    YESTERDAY = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=1)

    def setUp(self):
        super(AccessTestCase, self).setUp()
        course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')
        self.course = course_key.make_usage_key('course', course_key.run)
        self.anonymous_user = AnonymousUserFactory()
        self.beta_user = BetaTesterFactory(course_key=self.course.course_key)
        self.student = UserFactory()
        self.global_staff = UserFactory(is_staff=True)
        self.course_staff = StaffFactory(course_key=self.course.course_key)
        self.course_instructor = InstructorFactory(course_key=self.course.course_key)
        self.staff = GlobalStaffFactory()

    def verify_access(self, mock_unit, student_should_have_access, expected_error_type=None):
        """ Verify the expected result from _has_access_descriptor """
        response = access._has_access_descriptor(self.anonymous_user, 'load',
                                                 mock_unit, course_key=self.course.course_key)
        self.assertEqual(student_should_have_access, bool(response))

        if expected_error_type is not None:
            self.assertIsInstance(response, expected_error_type)
            self.assertIsNotNone(response.to_json()['error_code'])

        self.assertTrue(
            access._has_access_descriptor(self.course_staff, 'load', mock_unit, course_key=self.course.course_key)
        )

    def test_has_access_to_course(self):
        self.assertFalse(access._has_access_to_course(
            None, 'staff', self.course.course_key
        ))

        self.assertFalse(access._has_access_to_course(
            self.anonymous_user, 'staff', self.course.course_key
        ))
        self.assertFalse(access._has_access_to_course(
            self.anonymous_user, 'instructor', self.course.course_key
        ))

        self.assertTrue(access._has_access_to_course(
            self.global_staff, 'staff', self.course.course_key
        ))
        self.assertTrue(access._has_access_to_course(
            self.global_staff, 'instructor', self.course.course_key
        ))

        # A user has staff access if they are in the staff group
        self.assertTrue(access._has_access_to_course(
            self.course_staff, 'staff', self.course.course_key
        ))
        self.assertFalse(access._has_access_to_course(
            self.course_staff, 'instructor', self.course.course_key
        ))

        # A user has staff and instructor access if they are in the instructor group
        self.assertTrue(access._has_access_to_course(
            self.course_instructor, 'staff', self.course.course_key
        ))
        self.assertTrue(access._has_access_to_course(
            self.course_instructor, 'instructor', self.course.course_key
        ))

        # A user does not have staff or instructor access if they are
        # not in either the staff or the the instructor group
        self.assertFalse(access._has_access_to_course(
            self.student, 'staff', self.course.course_key
        ))
        self.assertFalse(access._has_access_to_course(
            self.student, 'instructor', self.course.course_key
        ))

        self.assertFalse(access._has_access_to_course(
            self.student, 'not_staff_or_instructor', self.course.course_key
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
                bool(access._has_access_error_desc(user, action, descriptor, self.course.course_key)),
                expected_response
            )

        with self.assertRaises(ValueError):
            access._has_access_error_desc(self.course_instructor, 'not_load_or_staff', descriptor, self.course.course_key)

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
            self.beta_user, 'load', mock_unit, course_key=self.course.course_key)))

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

    def test__has_access_course_desc_can_enroll(self):
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
        self.assertTrue(access._has_access_course_desc(user, 'enroll', course))

        # Staff can always enroll even outside the open enrollment period
        user = StaffFactory.create(course_key=course.id)
        self.assertTrue(access._has_access_course_desc(user, 'enroll', course))

        # Non-staff cannot enroll if it is between the start and end dates and invitation only
        # and not specifically allowed
        course = Mock(
            enrollment_start=yesterday, enrollment_end=tomorrow,
            id=SlashSeparatedCourseKey('edX', 'test', '2012_Fall'), enrollment_domain='',
            invitation_only=True
        )
        user = UserFactory.create()
        self.assertFalse(access._has_access_course_desc(user, 'enroll', course))

        # Non-staff can enroll if it is between the start and end dates and not invitation only
        course = Mock(
            enrollment_start=yesterday, enrollment_end=tomorrow,
            id=SlashSeparatedCourseKey('edX', 'test', '2012_Fall'), enrollment_domain='',
            invitation_only=False
        )
        self.assertTrue(access._has_access_course_desc(user, 'enroll', course))

        # Non-staff cannot enroll outside the open enrollment period if not specifically allowed
        course = Mock(
            enrollment_start=tomorrow, enrollment_end=tomorrow,
            id=SlashSeparatedCourseKey('edX', 'test', '2012_Fall'), enrollment_domain='',
            invitation_only=False
        )
        self.assertFalse(access._has_access_course_desc(user, 'enroll', course))

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
        self.assertTrue(access._has_access_course_desc(user, 'see_in_catalog', course))
        self.assertTrue(access._has_access_course_desc(user, 'see_about_page', course))
        self.assertTrue(access._has_access_course_desc(staff, 'see_in_catalog', course))
        self.assertTrue(access._has_access_course_desc(staff, 'see_about_page', course))

        # Now set visibility to just about page
        course = Mock(
            id=SlashSeparatedCourseKey('edX', 'test', '2012_Fall'),
            catalog_visibility=CATALOG_VISIBILITY_ABOUT
        )
        self.assertFalse(access._has_access_course_desc(user, 'see_in_catalog', course))
        self.assertTrue(access._has_access_course_desc(user, 'see_about_page', course))
        self.assertTrue(access._has_access_course_desc(staff, 'see_in_catalog', course))
        self.assertTrue(access._has_access_course_desc(staff, 'see_about_page', course))

        # Now set visibility to none, which means neither in catalog nor about pages
        course = Mock(
            id=SlashSeparatedCourseKey('edX', 'test', '2012_Fall'),
            catalog_visibility=CATALOG_VISIBILITY_NONE
        )
        self.assertFalse(access._has_access_course_desc(user, 'see_in_catalog', course))
        self.assertFalse(access._has_access_course_desc(user, 'see_about_page', course))
        self.assertTrue(access._has_access_course_desc(staff, 'see_in_catalog', course))
        self.assertTrue(access._has_access_course_desc(staff, 'see_about_page', course))

    @ddt.data(True, False)
    @patch.dict("django.conf.settings.FEATURES", {'ACCESS_REQUIRE_STAFF_FOR_COURSE': True})
    def test_see_exists(self, ispublic):
        """
        Test if user can see course
        """
        user = UserFactory.create(is_staff=False)
        course = Mock(ispublic=ispublic)
        self.assertEquals(bool(access._has_access_course_desc(user, 'see_exists', course)), ispublic)

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_PREREQUISITE_COURSES': True, 'MILESTONES_APP': True})
    def test_access_on_course_with_pre_requisites(self):
        """
        Test course access when a course has pre-requisite course yet to be completed
        """
        seed_milestone_relationship_types()
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
        response = access._has_access_course_desc(user, 'view_courseware_with_prerequisites', course)
        self.assertFalse(response)
        self.assertIsInstance(response, access_response.MilestoneError)
        # Staff can always access course
        staff = StaffFactory.create(course_key=course.id)
        self.assertTrue(access._has_access_course_desc(staff, 'view_courseware_with_prerequisites', course))

        # User should be able access after completing required course
        fulfill_course_milestone(pre_requisite_course.id, user)
        self.assertTrue(access._has_access_course_desc(user, 'view_courseware_with_prerequisites', course))

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
            bool(access._has_access_course_desc(self.student, 'load_mobile', descriptor)),
            student_expected
        )
        self.assertEqual(bool(access._has_access_course_desc(self.staff, 'load_mobile', descriptor)), staff_expected)

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_PREREQUISITE_COURSES': True, 'MILESTONES_APP': True})
    def test_courseware_page_unfulfilled_prereqs(self):
        """
        Test courseware access when a course has pre-requisite course yet to be completed
        """
        seed_milestone_relationship_types()
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
        self.user_completed_pre_requisite = UserFactory.create()  # pylint: disable=invalid-name
        fulfill_course_milestone(self.user_completed_pre_requisite, self.course_started.id)
        self.user_staff = UserFactory.create(is_staff=True)
        self.user_anonymous = AnonymousUserFactory.create()

    ENROLL_TEST_DATA = list(itertools.product(
        ['user_normal', 'user_staff', 'user_anonymous'],
        ['enroll'],
        ['course_default', 'course_started', 'course_not_started', 'course_staff_only'],
    ))

    LOAD_TEST_DATA = list(itertools.product(
        ['user_normal', 'user_beta_tester', 'user_staff'],
        ['load'],
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

    @ddt.data(*(ENROLL_TEST_DATA + LOAD_TEST_DATA + LOAD_MOBILE_TEST_DATA + PREREQUISITES_TEST_DATA))
    @ddt.unpack
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
                See COURSE_OVERVIEW_SUPPORTED_ACTIONS for valid values.
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
