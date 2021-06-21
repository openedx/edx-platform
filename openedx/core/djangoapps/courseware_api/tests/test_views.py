"""
Tests for courseware API
"""
import unittest
from datetime import datetime
from urllib.parse import urlencode
from typing import Optional

from unittest import mock
import ddt
from completion.test_utils import CompletionWaffleTestMixin, submit_completions_for_testing
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test.client import RequestFactory

from edx_toggles.toggles.testutils import override_waffle_flag
from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.certificates.api import get_certificate_url
from lms.djangoapps.certificates.tests.factories import (
    GeneratedCertificateFactory, LinkedInAddToProfileConfigurationFactory
)
from lms.djangoapps.courseware.access_utils import ACCESS_DENIED, ACCESS_GRANTED
from lms.djangoapps.courseware.tabs import ExternalLinkCourseTab
from lms.djangoapps.courseware.tests.helpers import MasqueradeMixin
from lms.djangoapps.courseware.toggles import (
    COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES,
    COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES_STREAK_CELEBRATION,
    COURSEWARE_MICROFRONTEND_SPECIAL_EXAMS,
    COURSEWARE_MICROFRONTEND_PROCTORED_EXAMS,
    COURSEWARE_USE_LEARNING_SEQUENCES_API,
)
from lms.djangoapps.experiments.testutils import override_experiment_waffle_flag
from lms.djangoapps.experiments.utils import STREAK_DISCOUNT_EXPERIMENT_FLAG
from lms.djangoapps.verify_student.services import IDVerificationService
from common.djangoapps.student.models import (
    CourseEnrollment, CourseEnrollmentCelebration
)
from common.djangoapps.student.roles import CourseInstructorRole
from common.djangoapps.student.tests.factories import CourseEnrollmentCelebrationFactory, UserFactory
from openedx.core.djangoapps.agreements.api import create_integrity_signature
from openedx.core.djangoapps.agreements.toggles import ENABLE_INTEGRITY_SIGNATURE
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ItemFactory, ToyCourseFactory


User = get_user_model()


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class BaseCoursewareTests(SharedModuleStoreTestCase):
    """
    Base class for courseware API tests
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.store = modulestore()
        cls.course = ToyCourseFactory.create(
            end=datetime(2028, 1, 1, 1, 1, 1),
            enrollment_start=datetime(2020, 1, 1, 1, 1, 1),
            enrollment_end=datetime(2028, 1, 1, 1, 1, 1),
            emit_signals=True,
            modulestore=cls.store,
        )
        cls.chapter = ItemFactory(parent=cls.course, category='chapter')
        cls.sequence = ItemFactory(parent=cls.chapter, category='sequential', display_name='sequence')
        cls.unit = ItemFactory.create(parent=cls.sequence, category='vertical', display_name="Vertical")

        cls.user = UserFactory(
            username='student',
            email='user@example.com',
            password='foo',
            is_staff=False
        )
        cls.instructor = UserFactory(
            username='instructor',
            email='instructor@example.com',
            password='foo',
            is_staff=False
        )
        CourseInstructorRole(cls.course.id).add_users(cls.instructor)
        cls.url = f'/api/courseware/course/{cls.course.id}'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.store.delete_course(cls.course.id, cls.user.id)

    def setUp(self):
        super().setUp()
        self.client.login(username=self.user.username, password='foo')


@ddt.ddt
@override_waffle_flag(COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES, active=True)
@override_waffle_flag(COURSEWARE_MICROFRONTEND_PROGRESS_MILESTONES_STREAK_CELEBRATION, active=True)
class CourseApiTestViews(BaseCoursewareTests, MasqueradeMixin):
    """
    Tests for the courseware REST API
    """
    @classmethod
    def setUpClass(cls):
        BaseCoursewareTests.setUpClass()
        cls.course.tabs.append(ExternalLinkCourseTab.load('external_link', name='Zombo', link='http://zombo.com'))
        cls.course.tabs.append(
            ExternalLinkCourseTab.load('external_link', name='Hidden', link='http://hidden.com', is_hidden=True)
        )
        cls.store.update_item(cls.course, cls.user.id)
        LinkedInAddToProfileConfigurationFactory.create()
        CourseModeFactory(course_id=cls.course.id, mode_slug=CourseMode.AUDIT)
        CourseModeFactory(
            course_id=cls.course.id,
            mode_slug=CourseMode.VERIFIED,
            expiration_datetime=datetime(3028, 1, 1),
            min_price=149,
            sku='ABCD1234',
        )

    @ddt.data(
        (True, None, ACCESS_DENIED),
        (True, 'audit', ACCESS_DENIED),
        (True, 'verified', ACCESS_DENIED),
        (False, None, ACCESS_DENIED),
        (False, None, ACCESS_GRANTED),
    )
    @ddt.unpack
    @mock.patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    @mock.patch('openedx.core.djangoapps.courseware_api.views.CoursewareMeta.is_microfrontend_enabled_for_user')
    def test_course_metadata(self, logged_in, enrollment_mode, enable_anonymous, is_microfrontend_enabled_for_user):
        is_microfrontend_enabled_for_user.return_value = True
        check_public_access = mock.Mock()
        check_public_access.return_value = enable_anonymous
        with mock.patch('lms.djangoapps.courseware.access_utils.check_public_access', check_public_access):
            if not logged_in:
                self.client.logout()
            if enrollment_mode == 'verified':
                cert = GeneratedCertificateFactory.create(
                    user=self.user,
                    course_id=self.course.id,
                    status='downloadable',
                    mode='verified',
                )
            if enrollment_mode:
                CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)

            response = self.client.get(self.url)
            assert response.status_code == 200
            if enrollment_mode:
                enrollment = response.data['enrollment']
                assert enrollment_mode == enrollment['mode']
                assert enrollment['is_active']
                assert len(response.data['tabs']) == 6
                found = False
                for tab in response.data['tabs']:
                    if tab['type'] == 'external_link':
                        assert tab['url'] != 'http://hidden.com', "Hidden tab is not hidden"
                        if tab['url'] == 'http://zombo.com':
                            found = True
                assert found, 'external link not in course tabs'

                assert not response.data['user_has_passing_grade']
                if enrollment_mode == 'audit':
                    assert response.data['verify_identity_url'] is None
                    assert response.data['verification_status'] == 'none'  # lint-amnesty, pylint: disable=literal-comparison
                    assert response.data['linkedin_add_to_profile_url'] is None
                else:
                    assert response.data['certificate_data']['cert_status'] == 'earned_but_not_available'
                    expected_verify_identity_url = IDVerificationService.get_verify_location(
                        course_id=self.course.id
                    )
                    # The response contains an absolute URL so this is only checking the path of the final
                    assert expected_verify_identity_url in response.data['verify_identity_url']
                    assert response.data['verification_status'] == 'none'  # lint-amnesty, pylint: disable=literal-comparison

                    request = RequestFactory().request()
                    cert_url = get_certificate_url(course_id=self.course.id, uuid=cert.verify_uuid)
                    linkedin_url_params = {
                        'name': '{platform_name} Verified Certificate for {course_name}'.format(
                            platform_name=settings.PLATFORM_NAME, course_name=self.course.display_name,
                        ),
                        'certUrl': request.build_absolute_uri(cert_url),
                        # default value from the LinkedInAddToProfileConfigurationFactory company_identifier
                        'organizationId': 1337,
                        'certId': cert.verify_uuid,
                        'issueYear': cert.created_date.year,
                        'issueMonth': cert.created_date.month,
                    }
                    expected_linkedin_url = (
                        'https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&{params}'.format(
                            params=urlencode(linkedin_url_params)
                        )
                    )
                    assert response.data['linkedin_add_to_profile_url'] == expected_linkedin_url
            elif enable_anonymous and not logged_in:
                # multiple checks use this handler
                check_public_access.assert_called()
                assert response.data['enrollment']['mode'] is None
                assert response.data['can_load_courseware']['has_access']
            else:
                assert not response.data['can_load_courseware']['has_access']

    @ddt.data(
        # Who has access to MFE courseware?
        {
            # Enrolled learners should have access.
            "mfe_is_visible": True,
            "username": "student",
            "enroll_user": True,
            "masquerade_role": None,
            "expect_can_load_courseware": True,
        },
        {
            # Un-enrolled learners should NOT have access.
            "mfe_is_visible": True,
            "username": "student",
            "enroll_user": False,
            "masquerade_role": None,
            "expect_can_load_courseware": False,
        },
        {
            # Un-enrolled instructors should have access.
            "mfe_is_visible": True,
            "username": "instructor",
            "enroll_user": False,
            "masquerade_role": None,
            "expect_can_load_courseware": True,
        },
        {
            # Un-enrolled instructors masquerading as students should have access.
            "mfe_is_visible": True,
            "username": "instructor",
            "enroll_user": False,
            "masquerade_role": "student",
            "expect_can_load_courseware": True,
        },
        {
            # If MFE is not visible, enrolled learners shouldn't have access.
            "mfe_is_visible": False,
            "username": "student",
            "enroll_user": True,
            "masquerade_role": None,
            "expect_can_load_courseware": False,
        },
        {
            # If MFE is not visible, instructors shouldn't have access.
            "mfe_is_visible": False,
            "username": "instructor",
            "enroll_user": False,
            "masquerade_role": None,
            "expect_can_load_courseware": False,
        },
        {
            # If MFE is not visible, masquerading instructors shouldn't have access.
            "mfe_is_visible": False,
            "username": "instructor",
            "enroll_user": False,
            "masquerade_role": "student",
            "expect_can_load_courseware": False,
        },
    )
    @ddt.unpack
    def test_can_load_courseware(
            self,
            mfe_is_visible: bool,
            username: str,
            enroll_user: bool,
            masquerade_role: Optional[str],
            expect_can_load_courseware: bool,
    ):
        """
        Test that can_load_courseware is calculated correctly based on
        access to MFE and access to the course itself.
        """
        user = User.objects.get(username=username)
        if enroll_user:
            CourseEnrollment.enroll(user, self.course.id, 'audit')

        patch_mfe_visible = mock.patch(
            'openedx.core.djangoapps.courseware_api.views.courseware_mfe_is_visible',
            return_value=mfe_is_visible,
        )
        self.client.login(username=user, password='foo')
        if masquerade_role:
            self.update_masquerade(role=masquerade_role)
        with patch_mfe_visible:
            response = self.client.get(self.url)

        assert response.status_code == 200
        if expect_can_load_courseware:
            assert response.data['can_load_courseware']['has_access']
        else:
            assert not response.data['can_load_courseware']['has_access']

    @ddt.data(True, False)
    def test_is_learning_sequences_api_enabled(self, enable_new_api):
        """
        Test that the Courseware API exposes the Learning Sequences API flag.
        """
        with override_waffle_flag(COURSEWARE_USE_LEARNING_SEQUENCES_API, active=enable_new_api):
            response = self.client.get(self.url)
            assert response.status_code == 200
            courseware_data = response.json()
            assert courseware_data['is_learning_sequences_api_enabled'] is enable_new_api

    def test_streak_data_in_response(self):
        """ Test that metadata endpoint returns data for the streak celebration """
        CourseEnrollment.enroll(self.user, self.course.id, 'audit')
        with override_experiment_waffle_flag(STREAK_DISCOUNT_EXPERIMENT_FLAG, active=True):
            with mock.patch('common.djangoapps.student.models.UserCelebration.perform_streak_updates', return_value=3):
                response = self.client.get(self.url, content_type='application/json')
                celebrations = response.json()['celebrations']
                assert celebrations['streak_length_to_celebrate'] == 3
                assert celebrations['streak_discount_experiment_enabled'] is True

    @ddt.data(
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    )
    @ddt.unpack
    def test_special_exams_enabled_for_course(self, is_globally_enabled, is_waffle_enabled):
        """ Ensure that special exams flag present in courseware meta data with expected value """
        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_SPECIAL_EXAMS': is_globally_enabled}):
            with override_waffle_flag(COURSEWARE_MICROFRONTEND_SPECIAL_EXAMS, active=is_waffle_enabled):
                response = self.client.get(self.url)
                assert response.status_code == 200
                courseware_data = response.json()
                assert 'is_mfe_special_exams_enabled' in courseware_data
                assert courseware_data['is_mfe_special_exams_enabled'] == (is_globally_enabled and is_waffle_enabled)

    @ddt.data(
        (None, False, False, False),
        ('verified', False, False, True),
        ('masters', False, False, True),
        ('audit', False, False, False),
        ('verified', False, True, False),
        ('masters', False, True, False),
        ('verified', True, False, False),
    )
    @ddt.unpack
    @override_waffle_flag(ENABLE_INTEGRITY_SIGNATURE, True)
    def test_user_needs_integrity_signature(
        self, enrollment_mode, is_staff, has_integrity_signature, needs_integrity_signature,
    ):
        """
        Test that the correct value is returned if the user needs to sign the integrity agreement for the course.
        """
        if is_staff:
            self.user.is_staff = True
            self.user.save()
        if enrollment_mode:
            CourseEnrollment.enroll(self.user, self.course.id, enrollment_mode)
        if has_integrity_signature:
            create_integrity_signature(self.user.username, str(self.course.id))
        response = self.client.get(self.url)
        assert response.status_code == 200
        courseware_data = response.json()
        assert 'user_needs_integrity_signature' in courseware_data
        assert courseware_data['user_needs_integrity_signature'] == needs_integrity_signature

    @ddt.data(
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    )
    @ddt.unpack
    def test_proctored_exams_enabled_for_course(self, is_globally_enabled, is_waffle_enabled):
        """ Ensure that proctored exams flag present in courseware meta data with expected value """
        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_SPECIAL_EXAMS': is_globally_enabled}):
            with override_waffle_flag(COURSEWARE_MICROFRONTEND_PROCTORED_EXAMS, active=is_waffle_enabled):
                response = self.client.get(self.url)
                assert response.status_code == 200
                courseware_data = response.json()
                assert 'is_mfe_proctored_exams_enabled' in courseware_data
                assert courseware_data['is_mfe_proctored_exams_enabled'] == (is_globally_enabled and is_waffle_enabled)


class SequenceApiTestViews(BaseCoursewareTests):
    """
    Tests for the sequence REST API
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = f'/api/courseware/sequence/{cls.sequence.location}'

    @classmethod
    def tearDownClass(cls):
        cls.store.delete_item(cls.sequence.location, cls.user.id)
        super().tearDownClass()

    def test_sequence_metadata(self):
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['display_name'] == 'sequence'
        assert len(response.data['items']) == 1


class ResumeApiTestViews(BaseCoursewareTests, CompletionWaffleTestMixin):
    """
    Tests for the resume API
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = f'/api/courseware/resume/{cls.course.id}'

    def test_resume_no_completion(self):
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['block_id'] is None
        assert response.data['unit_id'] is None
        assert response.data['section_id'] is None

    def test_resume_with_completion(self):
        self.override_waffle_switch(True)
        submit_completions_for_testing(self.user, [self.unit.location])
        response = self.client.get(self.url)
        assert response.status_code == 200
        assert response.data['block_id'] == str(self.unit.location)
        assert response.data['unit_id'] == str(self.unit.location)
        assert response.data['section_id'] == str(self.sequence.location)


@ddt.ddt
class CelebrationApiTestViews(BaseCoursewareTests, MasqueradeMixin):
    """
    Tests for the celebration API
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = f'/api/courseware/celebration/{cls.course.id}'

    def setUp(self):
        super().setUp()
        self.enrollment = CourseEnrollment.enroll(self.user, self.course.id, 'verified')

    @ddt.data(True, False)
    def test_happy_path(self, update):
        if update:
            CourseEnrollmentCelebrationFactory(enrollment=self.enrollment, celebrate_first_section=False)

        response = self.client.post(self.url, {'first_section': True}, content_type='application/json')
        assert response.status_code == (200 if update else 201)

        celebration = CourseEnrollmentCelebration.objects.first()
        assert celebration.celebrate_first_section
        assert celebration.enrollment.id == self.enrollment.id

    def test_extra_data(self):
        response = self.client.post(self.url, {'extra': True}, content_type='application/json')
        assert response.status_code == 400

    def test_no_data(self):
        response = self.client.post(self.url, {}, content_type='application/json')
        assert response.status_code == 200
        assert CourseEnrollmentCelebration.objects.count() == 0

    def test_no_enrollment(self):
        self.enrollment.delete()
        response = self.client.post(self.url, {'first_section': True}, content_type='application/json')
        assert response.status_code == 404

    def test_no_login(self):
        self.client.logout()
        response = self.client.post(self.url, {'first_section': True}, content_type='application/json')
        assert response.status_code == 401

    def test_invalid_course(self):
        response = self.client.post('/api/courseware/celebration/course-v1:does+not+exist',
                                    {'first_section': True}, content_type='application/json')
        assert response.status_code == 404

    def test_masquerade(self):
        self.user.is_staff = True
        self.user.save()

        user = UserFactory()
        CourseEnrollment.enroll(user, self.course.id, 'verified')

        response = self.client.post(self.url, {'first_section': True}, content_type='application/json')
        assert response.status_code == 201

        self.update_masquerade(username=user.username)
        response = self.client.post(self.url, {'first_section': False}, content_type='application/json')
        assert response.status_code == 202

        celebration = CourseEnrollmentCelebration.objects.first()
        assert celebration.celebrate_first_section  # make sure it didn't change during masquerade attempt
