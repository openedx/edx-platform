"""
Tests for users API
"""


import datetime

import ddt
import pytz
import six
from completion.test_utils import CompletionWaffleTestMixin, submit_completions_for_testing
from django.conf import settings
from django.template import defaultfilters
from django.test import RequestFactory, override_settings
from django.utils import timezone
from django.utils.timezone import now
from milestones.tests.utils import MilestonesTestCaseMixin
from mock import patch
from six.moves import range
from six.moves.urllib.parse import parse_qs

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.courseware.access_response import MilestoneAccessError, StartDateError, VisibilityError
from lms.djangoapps.certificates.api import generate_user_certificates
from lms.djangoapps.certificates.models import CertificateStatuses
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from lms.djangoapps.grades.tests.utils import mock_passing_grade
from lms.djangoapps.mobile_api.testutils import (
    MobileAPITestCase,
    MobileAuthTestMixin,
    MobileAuthUserTestMixin,
    MobileCourseAccessTestMixin
)
from lms.djangoapps.mobile_api.utils import API_V1, API_V05
from openedx.core.djangoapps.schedules.tests.factories import ScheduleFactory
from openedx.core.lib.courses import course_image_url
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from openedx.features.course_experience.tests.views.helpers import add_course_mode
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory
from common.djangoapps.util.milestones_helpers import set_prerequisite_courses
from common.djangoapps.util.testing import UrlResetMixin
from xmodule.course_module import DEFAULT_START_DATE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from .. import errors
from .serializers import CourseEnrollmentSerializer, CourseEnrollmentSerializerv05


@ddt.ddt
class TestUserDetailApi(MobileAPITestCase, MobileAuthUserTestMixin):
    """
    Tests for /api/mobile/{api_version}/users/<user_name>...
    """
    REVERSE_INFO = {'name': 'user-detail', 'params': ['username', 'api_version']}

    @ddt.data(API_V05, API_V1)
    def test_success(self, api_version):
        self.login()

        response = self.api_response(api_version=api_version)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['email'], self.user.email)


@ddt.ddt
class TestUserInfoApi(MobileAPITestCase, MobileAuthTestMixin):
    """
    Tests for /api/mobile/{api_version}/my_user_info
    """
    REVERSE_INFO = {'name': 'user-info', 'params': ['api_version']}

    @ddt.data(API_V05, API_V1)
    def test_success(self, api_version):
        """Verify the endpoint redirects to the user detail endpoint"""
        self.login()

        response = self.api_response(expected_response_code=302, api_version=api_version)
        self.assertIn(self.username, response['location'])

    @ddt.data(API_V05, API_V1)
    def test_last_loggedin_updated(self, api_version):
        """Verify that a user's last logged in value updates after hitting the my_user_info endpoint"""
        self.login()

        self.user.refresh_from_db()
        last_login_before = self.user.last_login

        # just hit the api endpoint; we don't care about the response here (tested previously)
        self.api_response(expected_response_code=302, api_version=api_version)

        self.user.refresh_from_db()
        last_login_after = self.user.last_login
        assert last_login_after > last_login_before


@ddt.ddt
@override_settings(MKTG_URLS={'ROOT': 'dummy-root'})
class TestUserEnrollmentApi(UrlResetMixin, MobileAPITestCase, MobileAuthUserTestMixin,
                            MobileCourseAccessTestMixin, MilestonesTestCaseMixin):
    """
    Tests for /api/mobile/{api_version}/users/<user_name>/course_enrollments/
    """
    REVERSE_INFO = {'name': 'courseenrollment-detail', 'params': ['username', 'api_version']}
    ALLOW_ACCESS_TO_UNRELEASED_COURSE = True
    ALLOW_ACCESS_TO_MILESTONE_COURSE = True
    ALLOW_ACCESS_TO_NON_VISIBLE_COURSE = True
    NEXT_WEEK = datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=7)
    LAST_WEEK = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=7)
    THREE_YEARS_AGO = now() - datetime.timedelta(days=(365 * 3))
    ADVERTISED_START = "Spring 2016"
    ENABLED_SIGNALS = ['course_published']
    DATES = {
        'next_week': NEXT_WEEK,
        'last_week': LAST_WEEK,
        'default_start_date': DEFAULT_START_DATE,
    }

    @patch.dict(settings.FEATURES, {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(TestUserEnrollmentApi, self).setUp()

    def verify_success(self, response):
        """
        Verifies user course enrollment response for success
        """
        super(TestUserEnrollmentApi, self).verify_success(response)
        courses = response.data
        self.assertEqual(len(courses), 1)

        found_course = courses[0]['course']
        self.assertIn('courses/{}/about'.format(self.course.id), found_course['course_about'])
        self.assertIn('course_info/{}/updates'.format(self.course.id), found_course['course_updates'])
        self.assertIn('course_info/{}/handouts'.format(self.course.id), found_course['course_handouts'])
        self.assertEqual(found_course['id'], six.text_type(self.course.id))
        self.assertEqual(courses[0]['mode'], CourseMode.DEFAULT_MODE_SLUG)
        self.assertEqual(courses[0]['course']['subscription_id'], self.course.clean_id(padding_char='_'))

        expected_course_image_url = course_image_url(self.course)
        self.assertIsNotNone(expected_course_image_url)
        self.assertIn(expected_course_image_url, found_course['course_image'])
        self.assertIn(expected_course_image_url, found_course['media']['course_image']['uri'])

    def verify_failure(self, response, error_type=None):
        self.assertEqual(response.status_code, 200)
        courses = response.data
        self.assertEqual(len(courses), 0)

    @patch.dict(settings.FEATURES, {'ENABLE_MKTG_SITE': True})
    @ddt.data(API_V05, API_V1)
    def test_sort_order(self, api_version):
        self.login()

        num_courses = 3
        courses = []
        for course_index in range(num_courses):
            courses.append(CourseFactory.create(mobile_available=True))
            self.enroll(courses[course_index].id)

        # verify courses are returned in the order of enrollment, with most recently enrolled first.
        response = self.api_response(api_version=api_version)
        for course_index in range(num_courses):
            self.assertEqual(
                response.data[course_index]['course']['id'],
                six.text_type(courses[num_courses - course_index - 1].id)
            )

    @ddt.data(API_V05, API_V1)
    @patch.dict(settings.FEATURES, {
        'ENABLE_PREREQUISITE_COURSES': True,
        'DISABLE_START_DATES': False,
        'ENABLE_MKTG_SITE': True,
    })
    def test_courseware_access(self, api_version):
        self.login()

        course_with_prereq = CourseFactory.create(start=self.LAST_WEEK, mobile_available=True)
        prerequisite_course = CourseFactory.create()
        set_prerequisite_courses(course_with_prereq.id, [six.text_type(prerequisite_course.id)])

        # Create list of courses with various expected courseware_access responses and corresponding expected codes
        courses = [
            course_with_prereq,
            CourseFactory.create(start=self.NEXT_WEEK, mobile_available=True),
            CourseFactory.create(visible_to_staff_only=True, mobile_available=True),
            CourseFactory.create(start=self.LAST_WEEK, mobile_available=True, visible_to_staff_only=False),
        ]

        expected_error_codes = [
            MilestoneAccessError().error_code,  # 'unfulfilled_milestones'
            StartDateError(self.NEXT_WEEK).error_code,  # 'course_not_started'
            VisibilityError().error_code,  # 'not_visible_to_user'
            None,
        ]

        # Enroll in all the courses
        for course in courses:
            self.enroll(course.id)

        # Verify courses have the correct response through error code. Last enrolled course is first course in response
        response = self.api_response(api_version=api_version)
        for course_index in range(len(courses)):
            result = response.data[course_index]['course']['courseware_access']
            self.assertEqual(result['error_code'], expected_error_codes[::-1][course_index])

            if result['error_code'] is not None:
                self.assertFalse(result['has_access'])

    @ddt.data(
        ('next_week', ADVERTISED_START, ADVERTISED_START, "string", API_V05),
        ('next_week', ADVERTISED_START, ADVERTISED_START, "string", API_V1),
        ('next_week', None, defaultfilters.date(NEXT_WEEK, "DATE_FORMAT"), "timestamp", API_V05),
        ('next_week', None, defaultfilters.date(NEXT_WEEK, "DATE_FORMAT"), "timestamp", API_V1),
        ('next_week', '', defaultfilters.date(NEXT_WEEK, "DATE_FORMAT"), "timestamp", API_V05),
        ('next_week', '', defaultfilters.date(NEXT_WEEK, "DATE_FORMAT"), "timestamp", API_V1),
        ('default_start_date', ADVERTISED_START, ADVERTISED_START, "string", API_V05),
        ('default_start_date', ADVERTISED_START, ADVERTISED_START, "string", API_V1),
        ('default_start_date', '', None, "empty", API_V05),
        ('default_start_date', '', None, "empty", API_V1),
        ('default_start_date', None, None, "empty", API_V05),
        ('default_start_date', None, None, "empty", API_V1),
    )
    @ddt.unpack
    @patch.dict(settings.FEATURES, {'DISABLE_START_DATES': False, 'ENABLE_MKTG_SITE': True})
    def test_start_type_and_display(self, start, advertised_start, expected_display, expected_type, api_version):
        """
        Tests that the correct start_type and start_display are returned in the
        case the course has not started
        """
        self.login()
        course = CourseFactory.create(start=self.DATES[start], advertised_start=advertised_start, mobile_available=True)
        self.enroll(course.id)

        response = self.api_response(api_version=api_version)
        self.assertEqual(response.data[0]['course']['start_type'], expected_type)
        self.assertEqual(response.data[0]['course']['start_display'], expected_display)

    @ddt.data(API_V05, API_V1)
    @patch.dict(settings.FEATURES, {"ENABLE_DISCUSSION_SERVICE": True, 'ENABLE_MKTG_SITE': True})
    def test_discussion_url(self, api_version):
        self.login_and_enroll()

        response = self.api_response(api_version=api_version)
        response_discussion_url = response.data[0]['course']['discussion_url']
        self.assertIn('/api/discussion/v1/courses/{}'.format(self.course.id), response_discussion_url)

    @ddt.data(API_V05, API_V1)
    def test_org_query(self, api_version):
        self.login()

        # Create list of courses with various organizations
        courses = [
            CourseFactory.create(org='edX', mobile_available=True),
            CourseFactory.create(org='edX', mobile_available=True),
            CourseFactory.create(org='edX', mobile_available=True, visible_to_staff_only=True),
            CourseFactory.create(org='Proversity.org', mobile_available=True),
            CourseFactory.create(org='MITx', mobile_available=True),
            CourseFactory.create(org='HarvardX', mobile_available=True),
        ]

        # Enroll in all the courses
        for course in courses:
            self.enroll(course.id)

        response = self.api_response(data={'org': 'edX'}, api_version=api_version)

        # Test for 3 expected courses
        self.assertEqual(len(response.data), 3)

        # Verify only edX courses are returned
        for entry in response.data:
            self.assertEqual(entry['course']['org'], 'edX')

    def create_enrollment(self, expired):
        """
        Create an enrollment
        """
        if expired:
            course = CourseFactory.create(start=self.THREE_YEARS_AGO, mobile_available=True)
            enrollment = CourseEnrollmentFactory.create(
                user=self.user,
                course_id=course.id
            )
            enrollment.created = self.THREE_YEARS_AGO + datetime.timedelta(days=1)
            enrollment.save()

            ScheduleFactory(
                enrollment=enrollment
            )
        else:
            course = CourseFactory.create(start=self.LAST_WEEK, mobile_available=True)
            self.enroll(course.id)

        add_course_mode(course, mode_slug=CourseMode.AUDIT)
        add_course_mode(course)

    def _get_enrollment_data(self, api_version, expired):
        self.login()
        self.create_enrollment(expired)
        return self.api_response(api_version=api_version).data

    def _assert_enrollment_results(self, api_version, courses, num_courses_returned, gating_enabled=True):
        self.assertEqual(len(courses), num_courses_returned)

        if api_version == API_V05:
            if num_courses_returned:
                self.assertNotIn('audit_access_expires', courses[0])
        else:
            self.assertIn('audit_access_expires', courses[0])
            if gating_enabled:
                self.assertIsNotNone(courses[0].get('audit_access_expires'))

    @ddt.data(
        (API_V05, True, 0),
        (API_V05, False, 1),
        (API_V1, True, 1),
        (API_V1, False, 1),
    )
    @ddt.unpack
    def test_enrollment_with_gating(self, api_version, expired, num_courses_returned):
        '''
        Test that expired courses are only returned in v1 of API
        when waffle flag enabled, and un-expired courses always returned
        '''
        CourseDurationLimitConfig.objects.create(enabled=True, enabled_as_of=datetime.datetime(2015, 1, 1))
        courses = self._get_enrollment_data(api_version, expired)
        self._assert_enrollment_results(api_version, courses, num_courses_returned, True)

    @ddt.data(
        (API_V05, True, 1),
        (API_V05, False, 1),
        (API_V1, True, 1),
        (API_V1, False, 1),
    )
    @ddt.unpack
    def test_enrollment_no_gating(self, api_version, expired, num_courses_returned):
        '''
        Test that expired and non-expired courses returned if waffle flag is disabled
        regarless of version of API
        '''
        CourseDurationLimitConfig.objects.create(enabled=False)
        courses = self._get_enrollment_data(api_version, expired)
        self._assert_enrollment_results(api_version, courses, num_courses_returned, False)


@override_settings(MKTG_URLS={'ROOT': 'dummy-root'})
class TestUserEnrollmentCertificates(UrlResetMixin, MobileAPITestCase, MilestonesTestCaseMixin):
    """
    Tests for /api/mobile/{api_version}/users/<user_name>/course_enrollments/
    """
    REVERSE_INFO = {'name': 'courseenrollment-detail', 'params': ['username', 'api_version']}
    ENABLED_SIGNALS = ['course_published']

    def verify_pdf_certificate(self):
        """
        Verifies the correct URL is returned in the response
        for PDF certificates.
        """
        self.login_and_enroll()

        certificate_url = "http://test_certificate_url"
        GeneratedCertificateFactory.create(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified',
            download_url=certificate_url,
        )

        response = self.api_response()
        certificate_data = response.data[0]['certificate']
        self.assertEqual(certificate_data['url'], certificate_url)

    @patch.dict(settings.FEATURES, {'ENABLE_MKTG_SITE': True})
    def test_no_certificate(self):
        self.login_and_enroll()

        response = self.api_response()
        certificate_data = response.data[0]['certificate']
        self.assertDictEqual(certificate_data, {})

    @patch.dict(settings.FEATURES, {'CERTIFICATES_HTML_VIEW': False, 'ENABLE_MKTG_SITE': True})
    def test_pdf_certificate_with_html_cert_disabled(self):
        """
        Tests PDF certificates with CERTIFICATES_HTML_VIEW set to True.
        """
        self.verify_pdf_certificate()

    @patch.dict(settings.FEATURES, {'CERTIFICATES_HTML_VIEW': True, 'ENABLE_MKTG_SITE': True})
    def test_pdf_certificate_with_html_cert_enabled(self):
        """
        Tests PDF certificates with CERTIFICATES_HTML_VIEW set to True.
        """
        self.verify_pdf_certificate()

    @patch.dict(settings.FEATURES, {'CERTIFICATES_HTML_VIEW': True, 'ENABLE_MKTG_SITE': True})
    def test_web_certificate(self):
        CourseMode.objects.create(
            course_id=self.course.id,
            mode_display_name="Honor",
            mode_slug=CourseMode.HONOR,
        )
        self.login_and_enroll()
        self.course.cert_html_view_enabled = True
        self.store.update_item(self.course, self.user.id)

        with mock_passing_grade():
            generate_user_certificates(self.user, self.course.id)

        response = self.api_response()
        certificate_data = response.data[0]['certificate']
        self.assertRegex(
            certificate_data['url'],
            r'http.*/certificates/[0-9a-f]{32}'
        )


class CourseStatusAPITestCase(MobileAPITestCase):
    """
    Base test class for /api/mobile/{api_version}/users/<user_name>/course_status_info/{course_id}
    """
    REVERSE_INFO = {'name': 'user-course-status', 'params': ['username', 'course_id', 'api_version']}

    def setUp(self):
        """
        Creates a basic course structure for our course
        """
        super(CourseStatusAPITestCase, self).setUp()

        self.section = ItemFactory.create(
            parent=self.course,
            category='chapter',
        )
        self.sub_section = ItemFactory.create(
            parent=self.section,
            category='sequential',
        )
        self.unit = ItemFactory.create(
            parent=self.sub_section,
            category='vertical',
        )
        self.other_sub_section = ItemFactory.create(
            parent=self.section,
            category='sequential',
        )
        self.other_unit = ItemFactory.create(
            parent=self.other_sub_section,
            category='vertical',
        )


class TestCourseStatusGET(CourseStatusAPITestCase, MobileAuthUserTestMixin,
                          MobileCourseAccessTestMixin, MilestonesTestCaseMixin, CompletionWaffleTestMixin):
    """
    Tests for GET of /api/mobile/v<version_number>/users/<user_name>/course_status_info/{course_id}
    """
    def test_success_v0(self):
        self.login_and_enroll()

        response = self.api_response(api_version=API_V05)
        self.assertEqual(
            response.data["last_visited_module_id"],
            six.text_type(self.sub_section.location)
        )
        self.assertEqual(
            response.data["last_visited_module_path"],
            [six.text_type(module.location) for module in [self.sub_section, self.section, self.course]]
        )

    def test_success_v1(self):
        self.override_waffle_switch(True)
        self.login_and_enroll()
        submit_completions_for_testing(self.user, [self.unit.location])
        response = self.api_response(api_version=API_V1)
        self.assertEqual(
            response.data["last_visited_block_id"],
            six.text_type(self.unit.location)
        )


class TestCourseStatusPATCH(CourseStatusAPITestCase, MobileAuthUserTestMixin,
                            MobileCourseAccessTestMixin, MilestonesTestCaseMixin):
    """
    Tests for PATCH of /api/mobile/v0.5/users/<user_name>/course_status_info/{course_id}
    """
    def url_method(self, url, **kwargs):  # pylint: disable=arguments-differ
        # override implementation to use PATCH method.
        return self.client.patch(url, data=kwargs.get('data', None))

    def test_success(self):
        self.login_and_enroll()
        response = self.api_response(data={"last_visited_module_id": six.text_type(self.other_unit.location)})
        self.assertEqual(
            response.data["last_visited_module_id"],
            six.text_type(self.other_sub_section.location)
        )

    def test_invalid_module(self):
        self.login_and_enroll()
        response = self.api_response(data={"last_visited_module_id": "abc"}, expected_response_code=400)
        self.assertEqual(
            response.data,
            errors.ERROR_INVALID_MODULE_ID
        )

    def test_nonexistent_module(self):
        self.login_and_enroll()
        non_existent_key = self.course.id.make_usage_key('video', 'non-existent')
        response = self.api_response(data={"last_visited_module_id": non_existent_key}, expected_response_code=400)
        self.assertEqual(
            response.data,
            errors.ERROR_INVALID_MODULE_ID
        )

    def test_no_timezone(self):
        self.login_and_enroll()
        past_date = datetime.datetime.now()
        response = self.api_response(
            data={
                "last_visited_module_id": six.text_type(self.other_unit.location),
                "modification_date": past_date.isoformat()
            },
            expected_response_code=400
        )
        self.assertEqual(
            response.data,
            errors.ERROR_INVALID_MODIFICATION_DATE
        )

    def _date_sync(self, date, initial_unit, update_unit, expected_subsection):
        """
        Helper for test cases that use a modification to decide whether
        to update the course status
        """
        self.login_and_enroll()

        # save something so we have an initial date
        self.api_response(data={"last_visited_module_id": six.text_type(initial_unit.location)})

        # now actually update it
        response = self.api_response(
            data={
                "last_visited_module_id": six.text_type(update_unit.location),
                "modification_date": date.isoformat()
            }
        )
        self.assertEqual(
            response.data["last_visited_module_id"],
            six.text_type(expected_subsection.location)
        )

    def test_old_date(self):
        self.login_and_enroll()
        date = timezone.now() + datetime.timedelta(days=-100)
        self._date_sync(date, self.unit, self.other_unit, self.sub_section)

    def test_new_date(self):
        self.login_and_enroll()
        date = timezone.now() + datetime.timedelta(days=100)
        self._date_sync(date, self.unit, self.other_unit, self.other_sub_section)

    def test_no_initial_date(self):
        self.login_and_enroll()
        response = self.api_response(
            data={
                "last_visited_module_id": six.text_type(self.other_unit.location),
                "modification_date": timezone.now().isoformat()
            }
        )
        self.assertEqual(
            response.data["last_visited_module_id"],
            six.text_type(self.other_sub_section.location)
        )

    def test_invalid_date(self):
        self.login_and_enroll()
        response = self.api_response(data={"modification_date": "abc"}, expected_response_code=400)
        self.assertEqual(
            response.data,
            errors.ERROR_INVALID_MODIFICATION_DATE
        )


@ddt.ddt
@patch.dict(settings.FEATURES, {'ENABLE_MKTG_SITE': True})
@override_settings(MKTG_URLS={'ROOT': 'dummy-root'})
class TestCourseEnrollmentSerializer(MobileAPITestCase, MilestonesTestCaseMixin):
    """
    Test the course enrollment serializer
    """
    ENABLED_SIGNALS = ['course_published']

    def setUp(self):
        super(TestCourseEnrollmentSerializer, self).setUp()
        self.login_and_enroll()
        self.request = RequestFactory().get('/')
        self.request.user = self.user

    def get_serialized_data(self, api_version):
        '''
        Return data from CourseEnrollmentSerializer
        '''
        if api_version == API_V05:
            serializer = CourseEnrollmentSerializerv05
        else:
            serializer = CourseEnrollmentSerializer

        return serializer(
            CourseEnrollment.enrollments_for_user(self.user)[0],
            context={'request': self.request, 'api_version': api_version},
        ).data

    def _expiration_in_response(self, response, api_version):
        '''
        Assert that audit_access_expires field in present in response
        based on version of api being used
        '''
        if api_version != API_V05:
            self.assertIn('audit_access_expires', response)
        else:
            self.assertNotIn('audit_access_expires', response)

    @ddt.data(API_V05, API_V1)
    def test_success(self, api_version):
        serialized = self.get_serialized_data(api_version)
        self.assertEqual(serialized['course']['name'], self.course.display_name)
        self.assertEqual(serialized['course']['number'], self.course.id.course)
        self.assertEqual(serialized['course']['org'], self.course.id.org)
        self._expiration_in_response(serialized, api_version)

        # Assert utm parameters
        qstwitter = parse_qs('utm_campaign=social-sharing-db&utm_medium=social&utm_source=twitter')
        qsfacebook = parse_qs('utm_campaign=social-sharing-db&utm_medium=social&utm_source=facebook')

        self.assertDictEqual(qsfacebook, parse_qs(serialized['course']['course_sharing_utm_parameters']['facebook']))
        self.assertDictEqual(qstwitter, parse_qs(serialized['course']['course_sharing_utm_parameters']['twitter']))

    @ddt.data(API_V05, API_V1)
    def test_with_display_overrides(self, api_version):
        self.course.display_coursenumber = "overridden_number"
        self.course.display_organization = "overridden_org"
        self.store.update_item(self.course, self.user.id)

        serialized = self.get_serialized_data(api_version)
        self.assertEqual(serialized['course']['number'], self.course.display_coursenumber)
        self.assertEqual(serialized['course']['org'], self.course.display_organization)
        self._expiration_in_response(serialized, api_version)
