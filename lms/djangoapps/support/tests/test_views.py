# coding: UTF-8
"""
Tests for support views.
"""


import itertools
import json
import re
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import ddt
import six
from django.contrib.auth.models import User
from django.db.models import signals
from django.http import HttpResponse
from django.urls import reverse
from mock import patch
from organizations.tests.factories import OrganizationFactory
from pytz import UTC
from social_django.models import UserSocialAuth

from common.test.utils import disable_signal
from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.program_enrollments.tests.factories import ProgramCourseEnrollmentFactory, ProgramEnrollmentFactory
from lms.djangoapps.support.serializers import ProgramEnrollmentSerializer
from lms.djangoapps.verify_student.models import VerificationDeadline
from lms.djangoapps.verify_student.services import IDVerificationService
from lms.djangoapps.verify_student.tests.factories import SSOVerificationFactory
from common.djangoapps.student.models import ENROLLED_TO_ENROLLED, CourseEnrollment, CourseEnrollmentAttribute, ManualEnrollmentAudit
from common.djangoapps.student.roles import GlobalStaff, SupportStaffRole
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from common.djangoapps.third_party_auth.tests.factories import SAMLProviderConfigFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class SupportViewTestCase(ModuleStoreTestCase):
    """
    Base class for support view tests.
    """

    USERNAME = "support"
    EMAIL = "support@example.com"
    PASSWORD = "support"

    def setUp(self):
        """Create a user and log in. """
        super(SupportViewTestCase, self).setUp()
        self.user = UserFactory(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        self.course = CourseFactory.create()
        success = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(success, msg="Could not log in")


class SupportViewManageUserTests(SupportViewTestCase):
    """
    Base class for support view tests.
    """

    def setUp(self):
        """Make the user support staff"""
        super(SupportViewManageUserTests, self).setUp()
        SupportStaffRole().add_users(self.user)

    def test_get_contact_us(self):
        """
        Tests Support View contact us Page
        """
        url = reverse('support:contact_us')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_password_assistance(self):
        """
        Tests password assistance
        """
        url = '/password_assistance'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_support_form(self):
        """
        Tests Support View to return Manage User Form
        """
        url = reverse('support:manage_user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_get_form_with_user_info(self):
        """
        Tests Support View to return Manage User Form
        with user info
        """
        url = reverse('support:manage_user_detail') + self.user.username
        response = self.client.get(url)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['username'], self.user.username)

    def test_disable_user_account(self):
        """
        Tests Support View to disable the user account
        """
        test_user = UserFactory(
            username='foobar', email='foobar@foobar.com', password='foobar'
        )
        url = reverse('support:manage_user_detail') + test_user.username
        response = self.client.post(url, data={
            'username_or_email': test_user.username,
            'comment': 'Test comment'
        })
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['success_msg'], 'User Disabled Successfully')
        test_user = User.objects.get(username=test_user.username, email=test_user.email)
        self.assertEqual(test_user.has_usable_password(), False)


@ddt.ddt
class SupportViewAccessTests(SupportViewTestCase):
    """
    Tests for access control of support views.
    """

    @ddt.data(*(
        (url_name, role, has_access)
        for (url_name, (role, has_access))
        in itertools.product((
            'support:index',
            'support:certificates',
            'support:enrollment',
            'support:enrollment_list',
            'support:manage_user',
            'support:manage_user_detail',
            'support:link_program_enrollments',
        ), (
            (GlobalStaff, True),
            (SupportStaffRole, True),
            (None, False)
        ))
    ))
    @ddt.unpack
    def test_access(self, url_name, role, has_access):
        if role is not None:
            role().add_users(self.user)

        url = reverse(url_name)
        response = self.client.get(url)

        if has_access:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertEqual(response.status_code, 403)

    @ddt.data(
        "support:index",
        "support:certificates",
        "support:enrollment",
        "support:enrollment_list",
        "support:manage_user",
        "support:manage_user_detail",
        "support:link_program_enrollments",
    )
    def test_require_login(self, url_name):
        url = reverse(url_name)

        # Log out then try to retrieve the page
        self.client.logout()
        response = self.client.get(url)

        # Expect a redirect to the login page
        redirect_url = "{login_url}?next={original_url}".format(
            login_url=reverse("signin_user"),
            original_url=url,
        )
        self.assertRedirects(response, redirect_url)


class SupportViewIndexTests(SupportViewTestCase):
    """
    Tests for the support index view.
    """

    EXPECTED_URL_NAMES = [
        "support:certificates",
        "support:link_program_enrollments",
    ]

    def setUp(self):
        """Make the user support staff. """
        super(SupportViewIndexTests, self).setUp()
        SupportStaffRole().add_users(self.user)

    def test_index(self):
        response = self.client.get(reverse("support:index"))
        self.assertContains(response, "Support")

        # Check that all the expected links appear on the index page.
        for url_name in self.EXPECTED_URL_NAMES:
            self.assertContains(response, reverse(url_name))


class SupportViewCertificatesTests(SupportViewTestCase):
    """
    Tests for the certificates support view.
    """
    def setUp(self):
        """Make the user support staff. """
        super(SupportViewCertificatesTests, self).setUp()
        SupportStaffRole().add_users(self.user)

    def test_certificates_no_filter(self):
        # Check that an empty initial filter is passed to the JavaScript client correctly.
        response = self.client.get(reverse("support:certificates"))
        self.assertContains(response, "userFilter: ''")

    def test_certificates_with_user_filter(self):
        # Check that an initial filter is passed to the JavaScript client.
        url = reverse("support:certificates") + "?user=student@example.com"
        response = self.client.get(url)
        self.assertContains(response, "userFilter: 'student@example.com'")

    def test_certificates_along_with_course_filter(self):
        # Check that an initial filter is passed to the JavaScript client.
        url = reverse("support:certificates") + "?user=student@example.com&course_id=" + six.text_type(self.course.id)
        response = self.client.get(url)
        self.assertContains(response, "userFilter: 'student@example.com'")
        self.assertContains(response, "courseFilter: '" + six.text_type(self.course.id) + "'")


@ddt.ddt
class SupportViewEnrollmentsTests(SharedModuleStoreTestCase, SupportViewTestCase):
    """Tests for the enrollment support view."""

    def setUp(self):
        super(SupportViewEnrollmentsTests, self).setUp()
        SupportStaffRole().add_users(self.user)

        self.course = CourseFactory(display_name=u'teꜱᴛ')
        self.student = UserFactory.create(username='student', email='test@example.com', password='test')

        for mode in (
                CourseMode.AUDIT, CourseMode.PROFESSIONAL, CourseMode.CREDIT_MODE,
                CourseMode.NO_ID_PROFESSIONAL_MODE, CourseMode.VERIFIED, CourseMode.HONOR
        ):
            CourseModeFactory.create(mode_slug=mode, course_id=self.course.id)

        self.verification_deadline = VerificationDeadline(
            course_key=self.course.id,
            deadline=datetime.now(UTC) + timedelta(days=365)
        )
        self.verification_deadline.save()

        CourseEnrollmentFactory.create(mode=CourseMode.AUDIT, user=self.student, course_id=self.course.id)

        self.url = reverse('support:enrollment_list', kwargs={'username_or_email': self.student.username})

    def assert_enrollment(self, mode):
        """
        Assert that the student's enrollment has the correct mode.
        """
        enrollment = CourseEnrollment.get_enrollment(self.student, self.course.id)
        self.assertEqual(enrollment.mode, mode)

    @ddt.data('username', 'email')
    def test_get_enrollments(self, search_string_type):
        url = reverse(
            'support:enrollment_list',
            kwargs={'username_or_email': getattr(self.student, search_string_type)}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data), 1)
        self.assertDictContainsSubset({
            'mode': CourseMode.AUDIT,
            'manual_enrollment': {},
            'user': self.student.username,
            'course_id': six.text_type(self.course.id),
            'is_active': True,
            'verified_upgrade_deadline': None,
        }, data[0])
        self.assertEqual(
            {CourseMode.VERIFIED, CourseMode.AUDIT, CourseMode.HONOR,
             CourseMode.NO_ID_PROFESSIONAL_MODE, CourseMode.PROFESSIONAL,
             CourseMode.CREDIT_MODE},
            {mode['slug'] for mode in data[0]['course_modes']}
        )

    def test_get_manual_enrollment_history(self):
        ManualEnrollmentAudit.create_manual_enrollment_audit(
            self.user,
            self.student.email,
            ENROLLED_TO_ENROLLED,
            'Financial Assistance',
            CourseEnrollment.objects.get(course_id=self.course.id, user=self.student)
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertDictContainsSubset({
            'enrolled_by': self.user.email,
            'reason': 'Financial Assistance',
        }, json.loads(response.content.decode('utf-8'))[0]['manual_enrollment'])

    @disable_signal(signals, 'post_save')
    @ddt.data('username', 'email')
    def test_change_enrollment(self, search_string_type):
        self.assertIsNone(ManualEnrollmentAudit.get_manual_enrollment_by_email(self.student.email))
        url = reverse(
            'support:enrollment_list',
            kwargs={'username_or_email': getattr(self.student, search_string_type)}
        )
        response = self.client.post(url, data={
            'course_id': six.text_type(self.course.id),
            'old_mode': CourseMode.AUDIT,
            'new_mode': CourseMode.VERIFIED,
            'reason': 'Financial Assistance'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(ManualEnrollmentAudit.get_manual_enrollment_by_email(self.student.email))
        self.assert_enrollment(CourseMode.VERIFIED)

    @ddt.data(
        ({}, r"The field \w+ is required."),
        ({'course_id': 'bad course key'}, 'Could not parse course key.'),
        ({
            'course_id': 'course-v1:TestX+T101+2015',
            'old_mode': CourseMode.AUDIT,
            'new_mode': CourseMode.VERIFIED,
            'reason': ''
        }, 'Could not find enrollment for user'),
        ({
            'course_id': None,
            'old_mode': CourseMode.HONOR,
            'new_mode': CourseMode.VERIFIED,
            'reason': ''
        }, r'User \w+ is not enrolled with mode ' + CourseMode.HONOR),
        ({
            'course_id': 'course-v1:TestX+T101+2015',
            'old_mode': CourseMode.AUDIT,
            'new_mode': CourseMode.CREDIT_MODE,
            'reason': 'Enrollment cannot be changed to credit mode'
        }, '')
    )
    @ddt.unpack
    def test_change_enrollment_bad_data(self, data, error_message):
        # `self` isn't available from within the DDT declaration, so
        # assign the course ID here
        if 'course_id' in data and data['course_id'] is None:
            data['course_id'] = str(self.course.id)
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(
            re.match(error_message, response.content.decode('utf-8').replace("'", '').replace('"', ''))
        )
        self.assert_enrollment(CourseMode.AUDIT)
        self.assertIsNone(ManualEnrollmentAudit.get_manual_enrollment_by_email(self.student.email))

    @disable_signal(signals, 'post_save')
    @ddt.data('honor', 'audit', 'verified', 'professional', 'no-id-professional', 'credit')
    def test_update_enrollment_for_all_modes(self, new_mode):
        """ Verify support can changed the enrollment to all available modes"""
        self.assert_update_enrollment('username', new_mode)

    @disable_signal(signals, 'post_save')
    @ddt.data('honor', 'audit', 'verified', 'professional', 'no-id-professional')
    def test_update_enrollment_for_ended_course(self, new_mode):
        """ Verify support can changed the enrollment of archived course. """
        self.set_course_end_date_and_expiry()
        self.assert_update_enrollment('username', new_mode)

    @ddt.data('username', 'email')
    def test_get_enrollments_with_expired_mode(self, search_string_type):
        """ Verify that page can get the all modes with archived course. """
        self.set_course_end_date_and_expiry()
        url = reverse(
            'support:enrollment_list',
            kwargs={'username_or_email': getattr(self.student, search_string_type)}
        )
        response = self.client.get(url)
        self._assert_generated_modes(response)

    @disable_signal(signals, 'post_save')
    @ddt.data('username', 'email')
    def test_update_enrollments_with_expired_mode(self, search_string_type):
        """ Verify that enrollment can be updated to verified mode. """
        self.set_course_end_date_and_expiry()
        self.assertIsNone(ManualEnrollmentAudit.get_manual_enrollment_by_email(self.student.email))
        self.assert_update_enrollment(search_string_type, CourseMode.VERIFIED)

    def _assert_generated_modes(self, response):
        """Dry method to generate course modes dict and test with response data."""
        modes = CourseMode.modes_for_course(self.course.id, include_expired=True, only_selectable=False)
        modes_data = []
        for mode in modes:
            expiry = mode.expiration_datetime.strftime('%Y-%m-%dT%H:%M:%SZ') if mode.expiration_datetime else None
            modes_data.append({
                'sku': mode.sku,
                'expiration_datetime': expiry,
                'name': mode.name,
                'currency': mode.currency,
                'bulk_sku': mode.bulk_sku,
                'min_price': mode.min_price,
                'suggested_prices': mode.suggested_prices,
                'slug': mode.slug,
                'description': mode.description
            })

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(data), 1)

        self.assertEqual(
            modes_data,
            data[0]['course_modes']
        )

        self.assertEqual(
            {CourseMode.VERIFIED, CourseMode.AUDIT, CourseMode.NO_ID_PROFESSIONAL_MODE,
             CourseMode.PROFESSIONAL, CourseMode.HONOR, CourseMode.CREDIT_MODE},
            {mode['slug'] for mode in data[0]['course_modes']}
        )

    def assert_update_enrollment(self, search_string_type, new_mode):
        """ Dry method to update the enrollment and assert response."""
        self.assertIsNone(ManualEnrollmentAudit.get_manual_enrollment_by_email(self.student.email))
        url = reverse(
            'support:enrollment_list',
            kwargs={'username_or_email': getattr(self.student, search_string_type)}
        )

        with patch('lms.djangoapps.support.views.enrollments.get_credit_provider_attribute_values') as mock_method:
            credit_provider = (
                [u'Arizona State University'], 'You are now eligible for credit from Arizona State University'
            )
            mock_method.return_value = credit_provider
            response = self.client.post(url, data={
                'course_id': six.text_type(self.course.id),
                'old_mode': CourseMode.AUDIT,
                'new_mode': new_mode,
                'reason': 'Financial Assistance'
            })

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(ManualEnrollmentAudit.get_manual_enrollment_by_email(self.student.email))
        self.assert_enrollment(new_mode)
        if new_mode == 'credit':
            enrollment_attr = CourseEnrollmentAttribute.objects.first()
            self.assertEqual(enrollment_attr.value, six.text_type(credit_provider[0]))

    def set_course_end_date_and_expiry(self):
        """ Set the course-end date and expire its verified mode."""
        self.course.start = datetime(year=1970, month=1, day=1, tzinfo=UTC)
        self.course.end = datetime(year=1970, month=1, day=10, tzinfo=UTC)

        # change verified mode expiry.
        verified_mode = CourseMode.objects.get(
            course_id=self.course.id,
            mode_slug=CourseMode.VERIFIED
        )
        verified_mode.expiration_datetime = datetime(year=1970, month=1, day=9, tzinfo=UTC)
        verified_mode.save()


@ddt.ddt
class SupportViewLinkProgramEnrollmentsTests(SupportViewTestCase):
    """
    Tests for the link_program_enrollments support view.
    """
    patch_render = patch(
        'lms.djangoapps.support.views.program_enrollments.render_to_response',
        return_value=HttpResponse(),
        autospec=True,
    )

    def setUp(self):
        """Make the user support staff. """
        super(SupportViewLinkProgramEnrollmentsTests, self).setUp()
        self.url = reverse("support:link_program_enrollments")
        SupportStaffRole().add_users(self.user)
        self.program_uuid = str(uuid4())
        self.text = '0001,user-0001\n0002,user-02'

    @patch_render
    def test_get(self, mocked_render):
        self.client.get(self.url)
        render_call_dict = mocked_render.call_args[0][1]
        assert render_call_dict == {
            'successes': [],
            'errors': [],
            'program_uuid': '',
            'text': ''
        }

    def test_rendering(self):
        """
        Test the view without mocking out the rendering like the rest of the tests.
        """
        response = self.client.get(self.url)
        content = six.text_type(response.content, encoding='utf-8')
        assert '"programUUID": ""' in content
        assert '"text": ""' in content

    @patch_render
    def test_invalid_uuid(self, mocked_render):
        self.client.post(self.url, data={
            'program_uuid': 'notauuid',
            'text': self.text,
        })
        msg = u"Supplied program UUID 'notauuid' is not a valid UUID."
        render_call_dict = mocked_render.call_args[0][1]
        assert render_call_dict['errors'] == [msg]

    @patch_render
    @ddt.data(
        ('program_uuid', ''),
        ('', 'text'),
        ('', ''),
    )
    @ddt.unpack
    def test_missing_parameter(self, program_uuid, text, mocked_render):
        error = (
            u"You must provide both a program uuid "
            u"and a series of lines with the format "
            u"'external_user_key,lms_username'."
        )
        self.client.post(self.url, data={
            'program_uuid': program_uuid,
            'text': text,
        })
        render_call_dict = mocked_render.call_args[0][1]
        assert render_call_dict['errors'] == [error]

    @ddt.data(
        '0001,learner-01\n0002,learner-02',                                 # normal
        '0001,learner-01,apple,orange\n0002,learner-02,purple',             # extra fields
        '\t0001        ,    \t  learner-01    \n   0002 , learner-02    ',  # whitespace
    )
    @patch('lms.djangoapps.support.views.program_enrollments.link_program_enrollments')
    def test_text(self, text, mocked_link):
        self.client.post(self.url, data={
            'program_uuid': self.program_uuid,
            'text': text,
        })
        mocked_link.assert_called_once()
        mocked_link.assert_called_with(
            UUID(self.program_uuid),
            {
                '0001': 'learner-01',
                '0002': 'learner-02',
            }
        )

    @patch_render
    def test_junk_text(self, mocked_render):
        text = 'alsdjflajsdflakjs'
        self.client.post(self.url, data={
            'program_uuid': self.program_uuid,
            'text': text,
        })
        msg = u"All linking lines must be in the format 'external_user_key,lms_username'"
        render_call_dict = mocked_render.call_args[0][1]
        assert render_call_dict['errors'] == [msg]

    def _setup_user_from_username(self, username):
        """
        Setup a user from the passed in username.
        If username passed in is falsy, return None
        """
        created_user = None
        if username:
            created_user = UserFactory(username=username, password=self.PASSWORD)
        return created_user

    def _setup_enrollments(self, external_user_key, linked_user=None):
        """
        Create enrollments for testing linking.
        The enrollments can be create with already linked edX user.
        """
        program_enrollment = ProgramEnrollmentFactory.create(
            external_user_key=external_user_key,
            program_uuid=self.program_uuid,
            user=linked_user
        )
        course_enrollment = None
        if linked_user:
            course_enrollment = CourseEnrollmentFactory.create(
                course_id=self.course.id,
                user=linked_user,
                mode=CourseMode.MASTERS,
                is_active=True
            )
        program_course_enrollment = ProgramCourseEnrollmentFactory.create(
            program_enrollment=program_enrollment,
            course_key=self.course.id,
            course_enrollment=course_enrollment,
            status='active'
        )

        return program_enrollment, program_course_enrollment

    @ddt.data(
        ('', None),
        ('linked_user', None),
        ('linked_user', 'original_user')
    )
    @ddt.unpack
    @patch_render
    def test_linking_program_enrollment(self, username, original_username, mocked_render):
        external_user_key = '0001'
        linked_user = self._setup_user_from_username(username)
        original_user = self._setup_user_from_username(original_username)
        program_enrollment, program_course_enrollment = self._setup_enrollments(
            external_user_key,
            original_user
        )
        self.client.post(self.url, data={
            'program_uuid': self.program_uuid,
            'text': external_user_key + ',' + username
        })
        render_call_dict = mocked_render.call_args[0][1]
        if username:
            expected_success = "('{}', '{}')".format(external_user_key, username)
            assert render_call_dict['successes'] == [expected_success]
            program_enrollment.refresh_from_db()
            assert program_enrollment.user == linked_user
            program_course_enrollment.refresh_from_db()
            assert program_course_enrollment.course_enrollment.user == linked_user
        else:
            error = u"All linking lines must be in the format 'external_user_key,lms_username'"
            assert render_call_dict['errors'] == [error]


@ddt.ddt
class ProgramEnrollmentsInspectorViewTests(SupportViewTestCase):
    """
    View tests for Program Enrollments Inspector
    """
    patch_render = patch(
        'lms.djangoapps.support.views.program_enrollments.render_to_response',
        return_value=HttpResponse(),
        autospec=True,
    )

    def setUp(self):
        super(ProgramEnrollmentsInspectorViewTests, self).setUp()
        self.url = reverse("support:program_enrollments_inspector")
        SupportStaffRole().add_users(self.user)
        self.program_uuid = str(uuid4())
        self.external_user_key = 'abcaaa'
        # Setup three orgs and their SAML providers
        self.org_key_list = ['test_org', 'donut_org', 'tri_org']
        for org_key in self.org_key_list:
            lms_org = OrganizationFactory(
                short_name=org_key
            )
            SAMLProviderConfigFactory(
                organization=lms_org,
                slug=org_key,
                enabled=True,
            )
        self.no_saml_org_key = 'no_saml_org'
        self.no_saml_lms_org = OrganizationFactory(
            short_name=self.no_saml_org_key
        )

    def _serialize_datetime(self, dt):
        return dt.strftime('%Y-%m-%dT%H:%M:%S')

    def test_initial_rendering(self):
        response = self.client.get(self.url)
        content = six.text_type(response.content, encoding='utf-8')
        expected_organization_serialized = '"orgKeys": {}'.format(
            json.dumps(sorted(self.org_key_list))
        )
        assert response.status_code == 200
        assert expected_organization_serialized in content
        assert '"learnerInfo": {}' in content

    def _construct_user(self, username, org_key=None, external_user_key=None):
        """
        Provided the username, create an edx account user. If the org_key is provided,
        SSO link the user with the IdP associated with org_key. Return the created user and
        expected user info object from the view
        """
        user = UserFactory(username=username)
        user_info = {
            'username': user.username,
            'email': user.email
        }
        if org_key and external_user_key:
            user_social_auth = UserSocialAuth.objects.create(
                user=user,
                uid='{0}:{1}'.format(org_key, external_user_key),
                provider='tpa-saml'
            )
            user_info['sso_list'] = [{
                'uid': user_social_auth.uid
            }]
        return user, user_info

    def _construct_enrollments(self, program_uuids, course_ids, external_user_key, edx_user=None):
        """
        A helper function to setup the program enrollments for a given learner.
        If the edx user is provided, it will try to SSO the user with the enrollments
        Return the expected info object that should be created based on the model setup
        """
        program_enrollments = []
        for program_uuid in program_uuids:
            course_enrollment = None
            program_enrollment = ProgramEnrollmentFactory.create(
                external_user_key=external_user_key,
                program_uuid=program_uuid,
                user=edx_user
            )

            for course_id in course_ids:
                if edx_user:
                    course_enrollment = CourseEnrollmentFactory.create(
                        course_id=course_id,
                        user=edx_user,
                        mode=CourseMode.MASTERS,
                        is_active=True
                    )

                program_course_enrollment = ProgramCourseEnrollmentFactory.create(
                    program_enrollment=program_enrollment,
                    course_key=course_id,
                    course_enrollment=course_enrollment,
                    status='active',
                )

            program_enrollments.append(program_enrollment)

        serialized = ProgramEnrollmentSerializer(program_enrollments, many=True)
        return serialized.data

    def _construct_id_verification(self, user):
        """
        Helper function to create the SSO verified record for the user
        so that the user is ID Verified
        """
        SSOVerificationFactory(
            identity_provider_slug=self.org_key_list[0],
            user=user,
        )
        return IDVerificationService.user_status(user)

    @patch_render
    def test_search_username_well_connected_user(self, mocked_render):
        created_user, expected_user_info = self._construct_user(
            'test_user_connected',
            self.org_key_list[0],
            self.external_user_key
        )
        id_verified = self._construct_id_verification(created_user)
        expected_enrollments = self._construct_enrollments(
            [self.program_uuid],
            [self.course.id],
            self.external_user_key,
            created_user
        )
        self.client.get(self.url, data={
            'edx_user': created_user.username,
            'org_key': self.org_key_list[0]
        })
        expected_info = {
            'user': expected_user_info,
            'enrollments': expected_enrollments,
            'id_verification': id_verified
        }

        render_call_dict = mocked_render.call_args[0][1]
        assert expected_info == render_call_dict['learner_program_enrollments']

    @patch_render
    def test_search_username_user_not_connected(self, mocked_render):
        created_user, expected_user_info = self._construct_user('user_not_connected')
        self.client.get(self.url, data={
            'edx_user': created_user.email,
            'org_key': self.org_key_list[0]
        })
        expected_info = {
            'user': expected_user_info,
            'id_verification': IDVerificationService.user_status(created_user)
        }

        render_call_dict = mocked_render.call_args[0][1]
        assert expected_info == render_call_dict['learner_program_enrollments']

    @patch_render
    def test_search_username_user_no_enrollment(self, mocked_render):
        created_user, expected_user_info = self._construct_user(
            'user_connected',
            self.org_key_list[0],
            self.external_user_key
        )
        self.client.get(self.url, data={
            'edx_user': created_user.email,
            'org_key': self.org_key_list[0]
        })
        expected_info = {
            'user': expected_user_info,
            'id_verification': IDVerificationService.user_status(created_user),
        }

        render_call_dict = mocked_render.call_args[0][1]
        assert expected_info == render_call_dict['learner_program_enrollments']

    @patch_render
    def test_search_username_user_no_course_enrollment(self, mocked_render):
        created_user, expected_user_info = self._construct_user(
            'user_connected',
            self.org_key_list[0],
            self.external_user_key
        )
        expected_enrollments = self._construct_enrollments(
            [self.program_uuid],
            [],
            self.external_user_key,
            created_user,
        )
        self.client.get(self.url, data={
            'edx_user': created_user.email,
            'org_key': self.org_key_list[0]
        })
        expected_info = {
            'user': expected_user_info,
            'enrollments': expected_enrollments,
            'id_verification': IDVerificationService.user_status(created_user),
        }

        render_call_dict = mocked_render.call_args[0][1]
        assert expected_info == render_call_dict['learner_program_enrollments']

    @patch_render
    def test_search_username_user_not_connected_with_enrollments(self, mocked_render):
        created_user, expected_user_info = self._construct_user(
            'user_not_connected'
        )
        self._construct_enrollments(
            [self.program_uuid],
            [],
            self.external_user_key,
        )
        self.client.get(self.url, data={
            'edx_user': created_user.email,
            'org_key': self.org_key_list[0]
        })
        expected_info = {
            'user': expected_user_info,
            'id_verification': IDVerificationService.user_status(created_user),
        }

        render_call_dict = mocked_render.call_args[0][1]
        assert expected_info == render_call_dict['learner_program_enrollments']

    @patch_render
    def test_search_username_user_id_verified(self, mocked_render):
        created_user, expected_user_info = self._construct_user(
            'user_not_connected'
        )
        id_verified = self._construct_id_verification(created_user)
        expected_info = {
            'user': expected_user_info,
            'id_verification': id_verified
        }

        self.client.get(self.url, data={
            'edx_user': created_user.email,
            'org_key': self.org_key_list[0]
        })

        render_call_dict = mocked_render.call_args[0][1]
        assert expected_info == render_call_dict['learner_program_enrollments']

    @patch_render
    def test_search_external_key_well_connected(self, mocked_render):
        created_user, expected_user_info = self._construct_user(
            'test_user_connected',
            self.org_key_list[0],
            self.external_user_key
        )
        expected_enrollments = self._construct_enrollments(
            [self.program_uuid],
            [self.course.id],
            self.external_user_key,
            created_user
        )
        id_verified = self._construct_id_verification(created_user)
        self.client.get(self.url, data={
            'external_user_key': self.external_user_key,
            'org_key': self.org_key_list[0]
        })
        expected_info = {
            'user': expected_user_info,
            'enrollments': expected_enrollments,
            'id_verification': id_verified,
        }

        render_call_dict = mocked_render.call_args[0][1]
        assert expected_info == render_call_dict['learner_program_enrollments']

    @ddt.data(
        ('', 'test_org'),
        ('bad_key', '')
    )
    @ddt.unpack
    @patch_render
    def test_search_no_external_user_key(self, user_key, org_key, mocked_render):
        self.client.get(self.url, data={
            'external_user_key': user_key,
            'org_key': org_key,
        })

        expected_error = (
            "To perform a search, you must provide either the student's "
            "(a) edX username, "
            "(b) email address associated with their edX account, or "
            "(c) Identity-providing institution and external key!"
        )

        render_call_dict = mocked_render.call_args[0][1]
        assert {} == render_call_dict['learner_program_enrollments']
        assert expected_error == render_call_dict['error']

    @patch_render
    def test_search_external_user_not_connected(self, mocked_render):
        expected_enrollments = self._construct_enrollments(
            [self.program_uuid],
            [self.course.id],
            self.external_user_key,
        )
        self.client.get(self.url, data={
            'external_user_key': self.external_user_key,
            'org_key': self.org_key_list[0]
        })
        expected_info = {
            'user': {
                'external_user_key': self.external_user_key,
            },
            'enrollments': expected_enrollments
        }

        render_call_dict = mocked_render.call_args[0][1]
        assert expected_info == render_call_dict['learner_program_enrollments']

    @patch_render
    def test_search_external_user_not_in_system(self, mocked_render):
        external_user_key = 'not_in_system'
        self.client.get(self.url, data={
            'external_user_key': external_user_key,
            'org_key': self.org_key_list[0],
        })

        expected_error = 'No user found for external key {} for institution {}'.format(
            external_user_key, self.org_key_list[0]
        )
        render_call_dict = mocked_render.call_args[0][1]
        assert expected_error == render_call_dict['error']


class SsoRecordsTests(SupportViewTestCase):

    def setUp(self):
        """Make the user support staff"""
        super(SsoRecordsTests, self).setUp()
        SupportStaffRole().add_users(self.user)
        self.student = UserFactory.create(username='student', email='test@example.com', password='test')
        self.url = reverse("support:sso_records", kwargs={'username_or_email': self.student.username})
        self.org_key_list = ['test_org']
        for org_key in self.org_key_list:
            lms_org = OrganizationFactory(
                short_name=org_key
            )
            SAMLProviderConfigFactory(
                organization=lms_org,
                slug=org_key,
                enabled=True,
            )

    def test_empty_response(self):
        response = self.client.get(self.url)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

    def test_user_does_not_exist(self):
        response = self.client.get(reverse("support:sso_records", kwargs={'username_or_email': 'wrong_username'}))
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

    def test_response(self):
        user_social_auth = UserSocialAuth.objects.create(
            user=self.student,
            uid=self.student.email,
            provider='tpa-saml'
        )
        response = self.client.get(self.url)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertContains(response, '"uid": "test@example.com"')
