"""
Unit tests for Contentstore views.
"""

from django.test.utils import override_settings
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.test import APITestCase

from lms.djangoapps.courseware.tests.factories import GlobalStaffFactory, InstructorFactory
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class ProctoringExamSettingsTestMixin():
    """ setup for proctored exam settings tests """
    def setUp(self):
        super().setUp()
        self.course_key = CourseKey.from_string('course-v1:edX+ToyX+Toy_Course')
        self.other_course_key = CourseKey.from_string('course-v1:edX+ToyX_Other_Course+Toy_Course')
        self.course = self.create_course_from_course_key(self.course_key)
        self.other_course = self.create_course_from_course_key(self.other_course_key)
        self.password = 'password'
        self.student = UserFactory.create(username='student', password=self.password)
        self.global_staff = GlobalStaffFactory(username='global-staff', password=self.password)
        self.course_instructor = InstructorFactory(
            username='instructor',
            password=self.password,
            course_key=self.course.id,
        )
        self.other_course_instructor = InstructorFactory(
            username='other-course-instructor',
            password=self.password,
            course_key=self.other_course.id,
        )

    def tearDown(self):
        super().tearDown()
        self.client.logout()

    @classmethod
    def create_course_from_course_key(cls, course_key):
        return CourseFactory.create(
            org=course_key.org,
            course=course_key.course,
            run=course_key.run
        )

    def make_request(self, course_id=None, data=None):
        raise NotImplementedError

    def get_url(self, course_key):
        return reverse(
            'cms.djangoapps.contentstore:v1:proctored_exam_settings',
            kwargs={'course_id': course_key}
        )

    def test_403_if_student(self):
        self.client.login(username=self.student.username, password=self.password)
        response = self.make_request()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_403_if_instructor_in_another_course(self):
        self.client.login(
            username=self.other_course_instructor.username,
            password=self.password
        )
        response = self.make_request()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_404_no_course_module(self):
        course_id = 'course-v1:edX+ToyX_Nonexistent_Course+Toy_Course'
        self.client.login(username=self.global_staff, password=self.password)
        response = self.make_request(course_id=course_id)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data == {
            'detail': 'Course with course_id {} does not exist.'.format(course_id)
        }


class ProctoringExamSettingsGetTests(ProctoringExamSettingsTestMixin, ModuleStoreTestCase, APITestCase):
    """ Tests for proctored exam settings GETs """
    @classmethod
    def get_expected_response_data(cls, course, user):
        return {
            'proctored_exam_settings': {
                'enable_proctored_exams': course.enable_proctored_exams,
                'allow_proctoring_opt_out': course.allow_proctoring_opt_out,
                'proctoring_provider': course.proctoring_provider,
                'proctoring_escalation_email': course.proctoring_escalation_email,
                'create_zendesk_tickets': course.create_zendesk_tickets,
            },
            'course_start_date': '2030-01-01T00:00:00Z',
            'available_proctoring_providers': ['null'],
        }

    def make_request(self, course_id=None, data=None):
        course_id = course_id if course_id else self.course.id
        url = self.get_url(course_id)
        return self.client.get(url)

    def test_200_global_staff(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        response = self.make_request()
        assert response.status_code == status.HTTP_200_OK
        assert response.data == self.get_expected_response_data(self.course, self.global_staff)

    def test_200_course_instructor(self):
        self.client.login(username=self.course_instructor.username, password=self.password)
        response = self.make_request()
        assert response.status_code == status.HTTP_200_OK
        assert response.data == self.get_expected_response_data(self.course, self.course_instructor)


class ProctoringExamSettingsPostTests(ProctoringExamSettingsTestMixin, ModuleStoreTestCase, APITestCase):
    """ Tests for proctored exam settings POST """

    @classmethod
    def get_request_data(  # pylint: disable=missing-function-docstring
        cls,
        enable_proctored_exams=False,
        allow_proctoring_opt_out=True,
        proctoring_provider='null',
        proctoring_escalation_email='example@edx.org',
        create_zendesk_tickets=True,
    ):
        return {
            'proctored_exam_settings': {
                'enable_proctored_exams': enable_proctored_exams,
                'allow_proctoring_opt_out': allow_proctoring_opt_out,
                'proctoring_provider': proctoring_provider,
                'proctoring_escalation_email': proctoring_escalation_email,
                'create_zendesk_tickets': create_zendesk_tickets,
            }
        }

    def make_request(self, course_id=None, data=None):
        course_id = course_id if course_id else self.course.id
        url = self.get_url(course_id)
        if data is None:
            data = self.get_request_data()
        return self.client.post(url, data, format='json')

    @override_settings(
        PROCTORING_BACKENDS={
            'DEFAULT': 'null',
            'proctortrack': {}
        },
    )
    def test_update_exam_settings_200_escalation_email(self):
        """ update exam settings for provider that requires an escalation email (proctortrack) """
        self.client.login(username=self.global_staff.username, password=self.password)
        data = self.get_request_data(
            enable_proctored_exams=True,
            proctoring_provider='proctortrack',
            proctoring_escalation_email='foo@bar.com',
        )
        response = self.make_request(data=data)

        # response is correct
        assert response.status_code == status.HTTP_200_OK
        self.assertDictEqual(response.data, {
            'proctored_exam_settings': {
                'enable_proctored_exams': True,
                'allow_proctoring_opt_out': True,
                'proctoring_provider': 'proctortrack',
                'proctoring_escalation_email': 'foo@bar.com',
                'create_zendesk_tickets': True,
            }
        })

        # course settings have been updated
        updated = modulestore().get_item(self.course.location)
        assert updated.enable_proctored_exams is True
        assert updated.proctoring_provider == 'proctortrack'
        assert updated.proctoring_escalation_email == 'foo@bar.com'

    @override_settings(
        PROCTORING_BACKENDS={
            'DEFAULT': 'null',
            'test_proctoring_provider': {}
        },
    )
    def test_update_exam_settings_200_no_escalation_email(self):
        """ escalation email may be blank if not required by the provider """
        self.client.login(username=self.global_staff.username, password=self.password)
        data = self.get_request_data(
            enable_proctored_exams=True,
            proctoring_provider='test_proctoring_provider',
            proctoring_escalation_email=None
        )
        response = self.make_request(data=data)

        # response is correct
        assert response.status_code == status.HTTP_200_OK
        self.assertDictEqual(response.data, {
            'proctored_exam_settings': {
                'enable_proctored_exams': True,
                'allow_proctoring_opt_out': True,
                'proctoring_provider': 'test_proctoring_provider',
                'proctoring_escalation_email': None,
                'create_zendesk_tickets': True,
            }
        })

        # course settings have been updated
        updated = modulestore().get_item(self.course.location)
        assert updated.enable_proctored_exams is True
        assert updated.proctoring_provider == 'test_proctoring_provider'
        assert updated.proctoring_escalation_email is None

    def test_update_exam_settings_excluded_field(self):
        """
        Excluded settings in POST data should not be updated
        """
        self.client.login(username=self.global_staff.username, password=self.password)
        data = self.get_request_data(
            proctoring_escalation_email='foo@bar.com',
        )
        response = self.make_request(data=data)

        # response is correct
        assert response.status_code == status.HTTP_200_OK
        self.assertDictEqual(response.data, {
            'proctored_exam_settings': {
                'enable_proctored_exams': False,
                'allow_proctoring_opt_out': True,
                'proctoring_provider': 'null',
                'proctoring_escalation_email': None,
                'create_zendesk_tickets': True,
            }
        })

        # excluded course settings are not updated
        updated = modulestore().get_item(self.course.location)
        assert updated.proctoring_escalation_email is None

    @override_settings(
        PROCTORING_BACKENDS={
            'DEFAULT': 'null',
            'test_proctoring_provider': {}
        },
    )
    def test_update_exam_settings_invalid_value(self):
        self.client.login(username=self.global_staff.username, password=self.password)
        data = self.get_request_data(
            enable_proctored_exams=True,
            proctoring_provider='notvalidprovider',
        )
        response = self.make_request(data=data)

        # response is correct
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        self.assertDictEqual(response.data, {
            'detail': [{
                'proctoring_provider': (
                    '[\"The selected proctoring provider, notvalidprovider, is not a valid provider. '
                    'Please select from one of [\'test_proctoring_provider\'].\"]'
                )
            }]
        })

        # course settings have been updated
        updated = modulestore().get_item(self.course.location)
        assert updated.enable_proctored_exams is False
        assert updated.proctoring_provider == 'null'

    def test_403_if_instructor_request_includes_opting_out_or_zendesk(self):
        self.client.login(username=self.course_instructor, password=self.password)
        data = self.get_request_data()
        response = self.make_request(data=data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @override_settings(
        PROCTORING_BACKENDS={
            'DEFAULT': 'null',
            'proctortrack': {}
        },
    )
    def test_200_for_instructor_request(self):
        self.client.login(username=self.course_instructor, password=self.password)
        data = {
            'proctored_exam_settings': {
                'enable_proctored_exams': True,
                'proctoring_provider': 'proctortrack',
                'proctoring_escalation_email': 'foo@bar.com',
            }
        }
        response = self.make_request(data=data)
        assert response.status_code == status.HTTP_200_OK
