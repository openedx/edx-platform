"""
Tests for auto generate certificate for open courses
"""
from __future__ import unicode_literals

from datetime import datetime, timedelta

import pytz
from django.core.management import call_command
from django.db.models import signals
from factory.django import mute_signals
from mock import Mock, patch

from lms.djangoapps.onboarding.tests.factories import UserFactory
from philu_commands.management.commands.auto_generate_certificates_for_open_courses import (
    is_course_valid_for_certificate_auto_generation
)
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestAutoGenerateCertificateForOpenCourse(ModuleStoreTestCase):
    """
    Tests for `auto_generate_certificates_for_open_courses.py` command.
    """

    @mute_signals(signals.pre_save, signals.post_save)
    def setUp(self):
        """
        This function is responsible for creating courses for every test and mocking the function for tests.
        """
        super(TestAutoGenerateCertificateForOpenCourse, self).setUp()
        self.course_1 = CourseFactory.create(display_name='test course 1', run='Testing_course_1')
        self.course_1.end = datetime.now(pytz.UTC) - timedelta(hours=2)
        self.user = UserFactory(username="test", email="test@example.com", password="123")

    @patch(
        'philu_commands.management.commands.auto_generate_certificates_for_open_courses._is_eligible_for_certificate',
        return_value=False)
    @patch('philu_commands.management.commands.auto_generate_certificates_for_open_courses.'
           'is_course_valid_for_certificate_auto_generation', return_value=True)
    @patch('philu_commands.management.commands.auto_generate_certificates_for_open_courses.modulestore')
    @patch(
        'philu_commands.management.commands.auto_generate_certificates_for_open_courses.CourseEnrollment.objects.filter'
    )
    @patch('philu_commands.management.commands.auto_generate_certificates_for_open_courses._get_cert_data')
    @patch('philu_commands.management.commands.auto_generate_certificates_for_open_courses.generate_user_certificates',
           return_value="generating")
    @patch('philu_commands.management.commands.auto_generate_certificates_for_open_courses.log.info')
    def test_successfully_generate_certificate(
        self,
        mock_log_info,
        mock_generate_user_certificates,
        mock__get_cert_data,
        mock_course_enrollments,
        mock_modulestore,
        _mock_is_course_valid,
        _mock__is_eligible_for_certificate
    ):
        """
        Test 'Successfully generate certificate'
        """
        mock_response = Mock(name="mock module store", **{"get_courses.return_value": [self.course_1]})
        mock_modulestore.return_value = mock_response
        mock_objects = CourseEnrollmentFactory.create(
            user=self.user, course_id=self.course_1.id, mode='honor')
        mock_course_enrollments.return_value = Mock(**{"all.return_value": [mock_objects], "get_items": {}})
        mock__get_cert_data.return_value = Mock(**{"cert_status": "requesting"})

        def assert_certificates_generated(info):
            """
            assert certification generation
            """
            certificate_success_message = 'Generating certificate for user with ' \
                                          'username: {} and user_id: {} with ' \
                                          'generation status: {}'.format(self.user.username, self.user.id,
                                                                         mock_generate_user_certificates())
            course_id_message = 'course id : {course_id}'.format(course_id=self.course_1.id)
            assert info in (certificate_success_message, course_id_message)

        mock_log_info.side_effect = assert_certificates_generated
        call_command('auto_generate_certificates_for_open_courses')
        mock_log_info.assert_called(2)

    @patch('philu_commands.management.commands.auto_generate_certificates_for_open_courses.modulestore')
    @patch('philu_commands.management.commands.auto_generate_certificates_for_open_courses.log.info')
    def test_no_open_course_available(self, mock_log_info, mock_modulestore):
        """
        Test 'If no open course is available'
        """
        mock_response = Mock(**{"get_courses.return_value": [self.course_1]})
        mock_modulestore.return_value = mock_response
        call_command('auto_generate_certificates_for_open_courses')
        assert not mock_log_info.called

    @patch('philu_commands.management.commands.auto_generate_certificates_for_open_courses.modulestore')
    @patch('philu_commands.management.commands.auto_generate_certificates_for_open_courses.log.info')
    def test_course_not_valid_for_certificate_auto_generation(self, mock_log_info, mock_modulestore):
        """
        Test 'If course is not valid'
        """
        mock_response = Mock(**{"get_courses.return_value": [self.course_1]})
        mock_modulestore.return_value = mock_response
        call_command('auto_generate_certificates_for_open_courses')
        assert not mock_log_info.called

    @patch('philu_commands.management.commands.auto_generate_certificates_for_open_courses.modulestore')
    @patch('philu_commands.management.commands.auto_generate_certificates_for_open_courses.log.info')
    @patch('philu_commands.management.commands.auto_generate_certificates_for_open_courses.'
           'is_course_valid_for_certificate_auto_generation')
    def test_course_valid_cert_data_not_exists(self, mock_is_course_valid, mock_log_info,
                                               mock_modulestore):
        """
        Test 'If course is valid but certification data does not exist'
        """
        mock_response = Mock(**{"get_courses.return_value": [self.course_1]})
        mock_modulestore.return_value = mock_response
        mock_is_course_valid.return_value = True
        call_command('auto_generate_certificates_for_open_courses')
        assert mock_log_info.called

    @patch('philu_commands.management.commands.auto_generate_certificates_for_open_courses.has_active_certificate',
           return_value=True)
    def test_is_course_valid_for_certificate_auto_generation(self, mock_has_active_certificate):
        """
        Test 'check if course is in active state'
        """
        self.course_1.has_started = Mock(return_value=True)
        self.course_1.has_ended = Mock(return_value=False)
        self.course_1.may_certify = Mock(return_value=True)
        mock_has_active_certificate.return_value = True
        assert is_course_valid_for_certificate_auto_generation(self.course_1) is True
