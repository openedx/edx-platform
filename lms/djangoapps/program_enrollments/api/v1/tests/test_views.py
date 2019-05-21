"""
Unit tests for ProgramEnrollment views.
"""
from __future__ import absolute_import, unicode_literals

import json
from uuid import uuid4

import ddt
import mock
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.test import APITestCase
from six import text_type
from six.moves import range, zip

from lms.djangoapps.courseware.tests.factories import GlobalStaffFactory
from lms.djangoapps.program_enrollments.api.v1.constants import MAX_ENROLLMENT_RECORDS, REQUEST_STUDENT_KEY
from lms.djangoapps.program_enrollments.api.v1.constants import CourseEnrollmentResponseStatuses as CourseStatuses
from lms.djangoapps.program_enrollments.models import ProgramEnrollment, ProgramCourseEnrollment
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from openedx.core.djangoapps.catalog.cache import PROGRAM_CACHE_KEY_TPL
from openedx.core.djangoapps.catalog.tests.factories import CourseFactory
from openedx.core.djangoapps.catalog.tests.factories import OrganizationFactory as CatalogOrganizationFactory
from openedx.core.djangoapps.catalog.tests.factories import ProgramFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangolib.testing.utils import CacheIsolationMixin
from .factories import ProgramCourseEnrollmentFactory, ProgramEnrollmentFactory


class ListViewTestMixin(object):
    """
    Mixin to define some shared test data objects for program/course enrollment
    list view tests.
    """
    view_name = None

    @classmethod
    def setUpClass(cls):
        super(ListViewTestMixin, cls).setUpClass()
        cls.program_uuid = '00000000-1111-2222-3333-444444444444'
        cls.curriculum_uuid = 'aaaaaaaa-1111-2222-3333-444444444444'
        cls.other_curriculum_uuid = 'bbbbbbbb-1111-2222-3333-444444444444'

        cls.course_id = CourseKey.from_string('course-v1:edX+ToyX+Toy_Course')
        _ = CourseOverviewFactory.create(id=cls.course_id)

        cls.password = 'password'
        cls.student = UserFactory.create(username='student', password=cls.password)
        cls.global_staff = GlobalStaffFactory.create(username='global-staff', password=cls.password)

    @classmethod
    def tearDownClass(cls):
        super(ListViewTestMixin, cls).tearDownClass()

    def get_url(self, program_uuid=None, course_id=None):
        """ Returns the primary URL requested by the test case. """
        kwargs = {'program_uuid': program_uuid or self.program_uuid}
        if course_id:
            kwargs['course_id'] = course_id or self.course_id

        return reverse(self.view_name, kwargs=kwargs)


class ProgramEnrollmentListTest(ListViewTestMixin, APITestCase):
    """
    Tests for GET calls to the Program Enrollments API.
    """
    view_name = 'programs_api:v1:program_enrollments'

    def create_program_enrollments(self):
        """
        Helper method for creating program enrollment records.
        """
        for i in range(2):
            user_key = 'user-{}'.format(i)
            ProgramEnrollmentFactory.create(
                program_uuid=self.program_uuid,
                curriculum_uuid=self.curriculum_uuid,
                user=None,
                status='pending',
                external_user_key=user_key,
            )

        for i in range(2, 4):
            user_key = 'user-{}'.format(i)
            ProgramEnrollmentFactory.create(
                program_uuid=self.program_uuid, curriculum_uuid=self.curriculum_uuid, external_user_key=user_key,
            )

        self.addCleanup(self.destroy_program_enrollments)

    def destroy_program_enrollments(self):
        """
        Deletes program enrollments associated with this test case's program_uuid.
        """
        ProgramEnrollment.objects.filter(program_uuid=self.program_uuid).delete()

    @mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True, return_value=None)
    def test_404_if_no_program_with_key(self, mock_get_programs):
        self.client.login(username=self.global_staff.username, password=self.password)
        response = self.client.get(self.get_url(self.program_uuid))
        assert status.HTTP_404_NOT_FOUND == response.status_code
        mock_get_programs.assert_called_once_with(uuid=self.program_uuid)

    def test_403_if_not_staff(self):
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.get(self.get_url(self.program_uuid))
        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_401_if_anonymous(self):
        response = self.client.get(self.get_url(self.program_uuid))
        assert status.HTTP_401_UNAUTHORIZED == response.status_code

    def test_200_empty_results(self):
        self.client.login(username=self.global_staff.username, password=self.password)

        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.client.get(self.get_url(self.program_uuid))

        assert status.HTTP_200_OK == response.status_code
        expected = {
            'next': None,
            'previous': None,
            'results': [],
        }
        assert expected == response.data

    def test_200_many_results(self):
        self.client.login(username=self.global_staff.username, password=self.password)

        self.create_program_enrollments()
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.client.get(self.get_url(self.program_uuid))

        assert status.HTTP_200_OK == response.status_code
        expected = {
            'next': None,
            'previous': None,
            'results': [
                {
                    'student_key': 'user-0', 'status': 'pending', 'account_exists': False,
                    'curriculum_uuid': text_type(self.curriculum_uuid),
                },
                {
                    'student_key': 'user-1', 'status': 'pending', 'account_exists': False,
                    'curriculum_uuid': text_type(self.curriculum_uuid),
                },
                {
                    'student_key': 'user-2', 'status': 'enrolled', 'account_exists': True,
                    'curriculum_uuid': text_type(self.curriculum_uuid),
                },
                {
                    'student_key': 'user-3', 'status': 'enrolled', 'account_exists': True,
                    'curriculum_uuid': text_type(self.curriculum_uuid),
                },
            ],
        }
        assert expected == response.data

    def test_200_many_pages(self):
        self.client.login(username=self.global_staff.username, password=self.password)

        self.create_program_enrollments()
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            url = self.get_url(self.program_uuid) + '?page_size=2'
            response = self.client.get(url)

            assert status.HTTP_200_OK == response.status_code
            expected_results = [
                {
                    'student_key': 'user-0', 'status': 'pending', 'account_exists': False,
                    'curriculum_uuid': text_type(self.curriculum_uuid),
                },
                {
                    'student_key': 'user-1', 'status': 'pending', 'account_exists': False,
                    'curriculum_uuid': text_type(self.curriculum_uuid),
                },
            ]
            assert expected_results == response.data['results']
            # there's going to be a 'cursor' query param, but we have no way of knowing it's value
            assert response.data['next'] is not None
            assert self.get_url(self.program_uuid) in response.data['next']
            assert '?cursor=' in response.data['next']
            assert response.data['previous'] is None

            next_response = self.client.get(response.data['next'])
            assert status.HTTP_200_OK == next_response.status_code
            next_expected_results = [
                {
                    'student_key': 'user-2', 'status': 'enrolled', 'account_exists': True,
                    'curriculum_uuid': text_type(self.curriculum_uuid),
                },
                {
                    'student_key': 'user-3', 'status': 'enrolled', 'account_exists': True,
                    'curriculum_uuid': text_type(self.curriculum_uuid),
                },
            ]
            assert next_expected_results == next_response.data['results']
            assert next_response.data['next'] is None
            # there's going to be a 'cursor' query param, but we have no way of knowing it's value
            assert next_response.data['previous'] is not None
            assert self.get_url(self.program_uuid) in next_response.data['previous']
            assert '?cursor=' in next_response.data['previous']


class ProgramCacheTestCaseMixin(CacheIsolationMixin):
    """
    Mixin for using program cache in tests
    """
    ENABLED_CACHES = ['default']

    def setup_catalog_cache(self, program_uuid, organization_key):
        """
        helper function to initialize a cached program with an single authoring_organization
        """
        catalog_org = CatalogOrganizationFactory.create(key=organization_key)
        program = ProgramFactory.create(
            uuid=program_uuid,
            authoring_organizations=[catalog_org]
        )
        cache.set(PROGRAM_CACHE_KEY_TPL.format(uuid=program_uuid), program, None)
        return program


@ddt.ddt
class BaseCourseEnrollmentTestsMixin(ProgramCacheTestCaseMixin):
    """
    A base for tests for course enrollment.
    Children should override self.request()
    """

    @classmethod
    def setUpClass(cls):
        super(BaseCourseEnrollmentTestsMixin, cls).setUpClass()
        cls.start_cache_isolation()
        cls.password = 'password'
        cls.student = UserFactory.create(username='student', password=cls.password)
        cls.global_staff = GlobalStaffFactory.create(username='global-staff', password=cls.password)

    @classmethod
    def tearDownClass(cls):
        cls.end_cache_isolation()
        super(BaseCourseEnrollmentTestsMixin, cls).tearDownClass()

    def setUp(self):
        super(BaseCourseEnrollmentTestsMixin, self).setUp()
        self.clear_caches()
        self.addCleanup(self.clear_caches)
        self.program_uuid = uuid4()
        self.organization_key = "orgkey"
        self.program = self.setup_catalog_cache(self.program_uuid, self.organization_key)
        self.course = self.program["courses"][0]
        self.course_run = self.course["course_runs"][0]
        self.course_key = CourseKey.from_string(self.course_run["key"])
        CourseOverviewFactory(id=self.course_key)
        self.course_not_in_program = CourseFactory()
        self.course_not_in_program_key = CourseKey.from_string(
            self.course_not_in_program["course_runs"][0]["key"]
        )
        CourseOverviewFactory(id=self.course_not_in_program_key)
        self.default_url = self.get_url(self.program_uuid, self.course_key)
        self.client.login(username=self.global_staff, password=self.password)

    def learner_enrollment(self, student_key, enrollment_status="active"):
        """
        Convenience method to create a learner enrollment record
        """
        return {"student_key": student_key, "status": enrollment_status}

    def get_url(self, program_uuid, course_id):
        """
        Convenience method to build a path for a program course enrollment request
        """
        return reverse(
            'programs_api:v1:program_course_enrollments',
            kwargs={
                'program_uuid': str(program_uuid),
                'course_id': str(course_id)
            }
        )

    def request(self, path, data):
        pass

    def create_program_enrollment(self, external_user_key, user=False):
        """
        Creates and returns a ProgramEnrollment for the given external_user_key and
        user if specified.
        """
        program_enrollment = ProgramEnrollmentFactory.create(
            external_user_key=external_user_key,
            program_uuid=self.program_uuid,
        )
        if user is not False:
            program_enrollment.user = user
            program_enrollment.save()
        return program_enrollment

    def create_program_course_enrollment(self, program_enrollment, course_status='active'):
        """
        Creates and returns a ProgramCourseEnrollment for the given program_enrollment and
        self.course_key, creating a CourseEnrollment if the program enrollment has a user
        """
        course_enrollment = None
        if program_enrollment.user:
            course_enrollment = CourseEnrollmentFactory.create(
                course_id=self.course_key,
                user=program_enrollment.user,
            )
            course_enrollment.is_active = course_status == "active"
            course_enrollment.save()
        return ProgramCourseEnrollmentFactory(
            program_enrollment=program_enrollment,
            course_key=self.course_key,
            course_enrollment=course_enrollment,
            status=course_status,
        )

    def create_program_and_course_enrollments(self, external_user_key, user=False, course_status='active'):
        program_enrollment = self.create_program_enrollment(external_user_key, user)
        return self.create_program_course_enrollment(program_enrollment, course_status=course_status)

    def assert_program_course_enrollment(self, external_user_key, expected_status, has_user):
        """
        Convenience method to assert that a ProgramCourseEnrollment exists,
        and potentially that a CourseEnrollment also exists
        """
        enrollment = ProgramCourseEnrollment.objects.get(
            program_enrollment__external_user_key=external_user_key,
            program_enrollment__program_uuid=self.program_uuid
        )
        self.assertEqual(expected_status, enrollment.status)
        self.assertEqual(self.course_key, enrollment.course_key)
        course_enrollment = enrollment.course_enrollment
        if has_user:
            self.assertIsNotNone(course_enrollment)
            self.assertEqual(expected_status == "active", course_enrollment.is_active)
            self.assertEqual(self.course_key, course_enrollment.course_id)
        else:
            self.assertIsNone(course_enrollment)

    def test_401_not_logged_in(self):
        self.client.logout()
        request_data = [self.learner_enrollment("learner-1")]
        response = self.request(self.default_url, request_data)
        self.assertEqual(401, response.status_code)

    def test_403_forbidden(self):
        self.client.logout()
        self.client.login(username=self.student, password=self.password)
        request_data = [self.learner_enrollment("learner-1")]
        response = self.request(self.default_url, request_data)
        self.assertEqual(403, response.status_code)

    def test_413_payload_too_large(self):
        request_data = [self.learner_enrollment(str(i)) for i in range(30)]
        response = self.request(self.default_url, request_data)
        self.assertEqual(413, response.status_code)

    def test_404_not_found(self):
        nonexistant_course_key = CourseKey.from_string("course-v1:fake+fake+fake")
        paths = [
            self.get_url(uuid4(), self.course_key),  # program not found
            self.get_url(self.program_uuid, nonexistant_course_key),  # course not found
            self.get_url(self.program_uuid, self.course_not_in_program_key),  # course not in program
        ]
        request_data = [self.learner_enrollment("learner-1")]
        for path_404 in paths:
            response = self.request(path_404, request_data)
            self.assertEqual(404, response.status_code)

    def test_duplicate_learner(self):
        request_data = [
            self.learner_enrollment("learner-1", "active"),
            self.learner_enrollment("learner-1", "active"),
        ]
        response = self.request(self.default_url, request_data)
        self.assertEqual(422, response.status_code)
        self.assertDictEqual(
            {
                "learner-1": CourseStatuses.DUPLICATED
            },
            response.data
        )

    def test_user_not_in_program(self):
        request_data = [
            self.learner_enrollment("learner-1"),
        ]
        response = self.request(self.default_url, request_data)
        self.assertEqual(422, response.status_code)
        self.assertDictEqual(
            {
                "learner-1": CourseStatuses.NOT_IN_PROGRAM,
            },
            response.data
        )

    def test_invalid_status(self):
        request_data = [self.learner_enrollment('learner-1', 'this-is-not-a-status')]
        response = self.request(self.default_url, request_data)
        self.assertEqual(422, response.status_code)
        self.assertDictEqual({'learner-1': CourseStatuses.INVALID_STATUS}, response.data)

    @ddt.data(
        [{'status': 'active'}],
        [{'student_key': '000'}],
        ["this isn't even a dict!"],
        [{'student_key': '000', 'status': 'active'}, "bad_data"],
        "not a list",
    )
    def test_422_unprocessable_entity_bad_data(self, request_data):
        response = self.request(self.default_url, request_data)
        self.assertEqual(response.status_code, 422)
        self.assertIn('invalid enrollment record', response.data)


class CourseEnrollmentPostTests(BaseCourseEnrollmentTestsMixin, APITestCase):
    """ Tests for course enrollment POST """

    def request(self, path, data):
        return self.client.post(path, data, format='json')

    def test_create_enrollments(self):
        self.create_program_enrollment('learner-1')
        self.create_program_enrollment('learner-2')
        self.create_program_enrollment('learner-3', user=None)
        self.create_program_enrollment('learner-4', user=None)
        post_data = [
            self.learner_enrollment("learner-1", "active"),
            self.learner_enrollment("learner-2", "inactive"),
            self.learner_enrollment("learner-3", "active"),
            self.learner_enrollment("learner-4", "inactive"),
        ]
        response = self.request(self.default_url, post_data)
        self.assertEqual(200, response.status_code)
        self.assertDictEqual(
            {
                "learner-1": "active",
                "learner-2": "inactive",
                "learner-3": "active",
                "learner-4": "inactive",
            },
            response.data
        )
        self.assert_program_course_enrollment("learner-1", "active", True)
        self.assert_program_course_enrollment("learner-2", "inactive", True)
        self.assert_program_course_enrollment("learner-3", "active", False)
        self.assert_program_course_enrollment("learner-4", "inactive", False)

    def test_user_already_enrolled_in_course(self):
        self.create_program_and_course_enrollments('learner-1')
        post_data = [self.learner_enrollment("learner-1")]
        response = self.request(self.default_url, post_data)
        self.assertEqual(422, response.status_code)
        self.assertDictEqual({'learner-1': CourseStatuses.CONFLICT}, response.data)

    def test_207_multistatus(self):
        self.create_program_enrollment('learner-1')
        post_data = [self.learner_enrollment("learner-1"), self.learner_enrollment("learner-2")]
        response = self.request(self.default_url, post_data)
        self.assertEqual(207, response.status_code)
        self.assertDictEqual(
            {'learner-1': CourseStatuses.ACTIVE, 'learner-2': CourseStatuses.NOT_IN_PROGRAM},
            response.data
        )


@ddt.ddt
class CourseEnrollmentPatchTests(BaseCourseEnrollmentTestsMixin, APITestCase):
    """ Tests for course enrollment PATCH """

    def request(self, path, data):
        return self.client.patch(path, data, format='json')

    def test_207_multistatus(self):
        self.create_program_and_course_enrollments('learner-1')
        post_data = [self.learner_enrollment("learner-1"), self.learner_enrollment("learner-2")]
        response = self.request(self.default_url, post_data)
        self.assertEqual(207, response.status_code)
        self.assertDictEqual(
            {'learner-1': CourseStatuses.ACTIVE, 'learner-2': CourseStatuses.NOT_IN_PROGRAM},
            response.data
        )

    def test_user_not_enrolled_in_course(self):
        self.create_program_enrollment('learner-1')
        patch_data = [self.learner_enrollment('learner-1')]
        response = self.request(self.default_url, patch_data)
        self.assertEqual(422, response.status_code)
        self.assertDictEqual({'learner-1': CourseStatuses.NOT_FOUND}, response.data)

    @ddt.data(
        ('active', 'inactive', 'active', 'inactive'),
        ('inactive', 'active', 'inactive', 'active'),
        ('active', 'active', 'active', 'active'),
        ('inactive', 'inactive', 'inactive', 'inactive'),
    )
    def test_change_status(self, initial_statuses):
        self.create_program_and_course_enrollments('learner-1', course_status=initial_statuses[0])
        self.create_program_and_course_enrollments('learner-2', course_status=initial_statuses[1])
        self.create_program_and_course_enrollments('learner-3', course_status=initial_statuses[2], user=None)
        self.create_program_and_course_enrollments('learner-4', course_status=initial_statuses[3], user=None)
        patch_data = [
            self.learner_enrollment('learner-1', 'inactive'),
            self.learner_enrollment('learner-2', 'active'),
            self.learner_enrollment('learner-3', 'inactive'),
            self.learner_enrollment('learner-4', 'active'),
        ]
        response = self.request(self.default_url, patch_data)
        self.assertEqual(200, response.status_code)
        self.assertDictEqual(
            {
                'learner-1': 'inactive',
                'learner-2': 'active',
                'learner-3': 'inactive',
                'learner-4': 'active',
            },
            response.data
        )
        self.assert_program_course_enrollment('learner-1', 'inactive', True)
        self.assert_program_course_enrollment('learner-2', 'active', True)
        self.assert_program_course_enrollment('learner-3', 'inactive', False)
        self.assert_program_course_enrollment('learner-4', 'active', False)


class ProgramCourseEnrollmentListTest(ListViewTestMixin, APITestCase):
    """
    Tests for GET calls to the Program Course Enrollments API.
    """
    view_name = 'programs_api:v1:program_course_enrollments'

    def create_course_enrollments(self):
        """ Helper method for creating ProgramCourseEnrollments. """
        program_enrollment_1 = ProgramEnrollmentFactory.create(
            program_uuid=self.program_uuid, curriculum_uuid=self.curriculum_uuid, external_user_key='user-0',
        )
        program_enrollment_2 = ProgramEnrollmentFactory.create(
            program_uuid=self.program_uuid, curriculum_uuid=self.other_curriculum_uuid, external_user_key='user-0',
        )
        ProgramCourseEnrollmentFactory.create(
            program_enrollment=program_enrollment_1,
            course_key=self.course_id,
            status='active',
        )
        ProgramCourseEnrollmentFactory.create(
            program_enrollment=program_enrollment_2,
            course_key=self.course_id,
            status='inactive',
        )

        self.addCleanup(self.destroy_course_enrollments)

    def destroy_course_enrollments(self):
        """ Helper method for tearing down ProgramCourseEnrollments. """
        ProgramCourseEnrollment.objects.filter(
            program_enrollment__program_uuid=self.program_uuid,
            course_key=self.course_id
        ).delete()

    @mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True, return_value=None)
    def test_404_if_no_program_with_key(self, mock_get_programs):
        self.client.login(username=self.global_staff.username, password=self.password)
        response = self.client.get(self.get_url(self.program_uuid, self.course_id))
        assert status.HTTP_404_NOT_FOUND == response.status_code
        mock_get_programs.assert_called_once_with(uuid=self.program_uuid)

    def test_404_if_course_does_not_exist(self):
        other_course_key = CourseKey.from_string('course-v1:edX+ToyX+Other_Course')
        self.client.login(username=self.global_staff.username, password=self.password)
        response = self.client.get(self.get_url(self.program_uuid, other_course_key))
        assert status.HTTP_404_NOT_FOUND == response.status_code

    def test_403_if_not_staff(self):
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.get(self.get_url(self.program_uuid, self.course_id))
        assert status.HTTP_403_FORBIDDEN == response.status_code

    def test_401_if_anonymous(self):
        response = self.client.get(self.get_url(self.program_uuid, self.course_id))
        assert status.HTTP_401_UNAUTHORIZED == response.status_code

    def test_200_empty_results(self):
        self.client.login(username=self.global_staff.username, password=self.password)

        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.client.get(self.get_url(self.program_uuid, self.course_id))

        assert status.HTTP_200_OK == response.status_code
        expected = {
            'next': None,
            'previous': None,
            'results': [],
        }
        assert expected == response.data

    def test_200_many_results(self):
        self.client.login(username=self.global_staff.username, password=self.password)

        self.create_course_enrollments()
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.client.get(self.get_url(self.program_uuid, self.course_id))

        assert status.HTTP_200_OK == response.status_code
        expected = {
            'next': None,
            'previous': None,
            'results': [
                {
                    'student_key': 'user-0', 'status': 'active', 'account_exists': True,
                    'curriculum_uuid': text_type(self.curriculum_uuid),
                },
                {
                    'student_key': 'user-0', 'status': 'inactive', 'account_exists': True,
                    'curriculum_uuid': text_type(self.other_curriculum_uuid),
                },
            ],
        }
        assert expected == response.data

    def test_200_many_pages(self):
        self.client.login(username=self.global_staff.username, password=self.password)

        self.create_course_enrollments()
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            url = self.get_url(self.program_uuid, self.course_id) + '?page_size=1'
            response = self.client.get(url)

            assert status.HTTP_200_OK == response.status_code
            expected_results = [
                {
                    'student_key': 'user-0', 'status': 'active', 'account_exists': True,
                    'curriculum_uuid': text_type(self.curriculum_uuid),
                },
            ]
            assert expected_results == response.data['results']
            # there's going to be a 'cursor' query param, but we have no way of knowing it's value
            assert response.data['next'] is not None
            assert self.get_url(self.program_uuid, self.course_id) in response.data['next']
            assert '?cursor=' in response.data['next']
            assert response.data['previous'] is None

            next_response = self.client.get(response.data['next'])
            assert status.HTTP_200_OK == next_response.status_code
            next_expected_results = [
                {
                    'student_key': 'user-0', 'status': 'inactive', 'account_exists': True,
                    'curriculum_uuid': text_type(self.other_curriculum_uuid),
                },
            ]
            assert next_expected_results == next_response.data['results']
            assert next_response.data['next'] is None
            # there's going to be a 'cursor' query param, but we have no way of knowing it's value
            assert next_response.data['previous'] is not None
            assert self.get_url(self.program_uuid, self.course_id) in next_response.data['previous']
            assert '?cursor=' in next_response.data['previous']


class ProgramEnrollmentViewPostTests(APITestCase):
    """
    Tests for the ProgramEnrollment view POST method.
    """
    def setUp(self):
        super(ProgramEnrollmentViewPostTests, self).setUp()
        global_staff = GlobalStaffFactory.create(username='global-staff', password='password')
        self.client.login(username=global_staff.username, password='password')

    def tearDown(self):
        super(ProgramEnrollmentViewPostTests, self).tearDown()
        ProgramEnrollment.objects.all().delete()

    def student_enrollment(self, enrollment_status, external_user_key=None):
        return {
            REQUEST_STUDENT_KEY: external_user_key or str(uuid4().hex[0:10]),
            'status': enrollment_status,
            'curriculum_uuid': str(uuid4())
        }

    def test_successful_program_enrollments_no_existing_user(self):
        program_key = uuid4()
        statuses = ['pending', 'enrolled', 'pending']
        external_user_keys = ['abc1', 'efg2', 'hij3']

        curriculum_uuid = uuid4()
        curriculum_uuids = [curriculum_uuid, curriculum_uuid, uuid4()]
        post_data = [
            {
                REQUEST_STUDENT_KEY: e,
                'status': s,
                'curriculum_uuid': str(c)
            }
            for e, s, c in zip(external_user_keys, statuses, curriculum_uuids)
        ]

        url = reverse('programs_api:v1:program_enrollments', args=[program_key])
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            with mock.patch(
                'lms.djangoapps.program_enrollments.api.v1.views.get_user_by_program_id',
                autospec=True,
                return_value=None
            ):
                response = self.client.post(url, json.dumps(post_data), content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for i in range(3):
            enrollment = ProgramEnrollment.objects.get(external_user_key=external_user_keys[i])

            self.assertEqual(enrollment.external_user_key, external_user_keys[i])
            self.assertEqual(enrollment.program_uuid, program_key)
            self.assertEqual(enrollment.status, statuses[i])
            self.assertEqual(enrollment.curriculum_uuid, curriculum_uuids[i])
            self.assertEqual(enrollment.user, None)

    def test_successful_program_enrollments_existing_user(self):
        program_key = uuid4()
        curriculum_uuid = uuid4()

        post_data = [
            {
                'status': 'enrolled',
                REQUEST_STUDENT_KEY: 'abc1',
                'curriculum_uuid': str(curriculum_uuid)
            }
        ]

        user = User.objects.create_user('test_user', 'test@example.com', 'password')

        url = reverse('programs_api:v1:program_enrollments', args=[program_key])

        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            with mock.patch(
                'lms.djangoapps.program_enrollments.api.v1.views.get_user_by_program_id',
                autospec=True,
                return_value=user
            ):
                response = self.client.post(url, json.dumps(post_data), content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        enrollment = ProgramEnrollment.objects.get(external_user_key='abc1')

        self.assertEqual(enrollment.external_user_key, 'abc1')
        self.assertEqual(enrollment.program_uuid, program_key)
        self.assertEqual(enrollment.status, 'enrolled')
        self.assertEqual(enrollment.curriculum_uuid, curriculum_uuid)
        self.assertEqual(enrollment.user, user)

    def test_enrollment_payload_limit(self):

        post_data = []
        for _ in range(MAX_ENROLLMENT_RECORDS + 1):
            post_data += self.student_enrollment('enrolled')

        url = reverse('programs_api:v1:program_enrollments', args=[uuid4()])
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            with mock.patch(
                'lms.djangoapps.program_enrollments.api.v1.views.get_user_by_program_id',
                autospec=True,
                return_value=None
            ):
                response = self.client.post(url, json.dumps(post_data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    def test_duplicate_enrollment(self):
        post_data = [
            self.student_enrollment('enrolled', '001'),
            self.student_enrollment('enrolled', '002'),
            self.student_enrollment('enrolled', '001'),
        ]

        url = reverse('programs_api:v1:program_enrollments', args=[uuid4()])
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            with mock.patch(
                'lms.djangoapps.program_enrollments.api.v1.views.get_user_by_program_id',
                autospec=True,
                return_value=None
            ):
                response = self.client.post(url, json.dumps(post_data), content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data, {
            '001': 'duplicated',
            '002': 'enrolled',
        })

    def test_unprocessable_enrollment(self):
        url = reverse('programs_api:v1:program_enrollments', args=[uuid4()])

        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            with mock.patch(
                'lms.djangoapps.program_enrollments.api.v1.views.get_user_by_program_id',
                autospec=True,
                return_value=None
            ):
                response = self.client.post(
                    url,
                    json.dumps([{'status': 'enrolled'}]),
                    content_type='application/json'
                )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_unauthenticated(self):
        self.client.logout()
        post_data = [
            self.student_enrollment('enrolled')
        ]
        url = reverse('programs_api:v1:program_enrollments', args=[uuid4()])
        response = self.client.post(
            url,
            json.dumps(post_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_program_unauthorized(self):
        student = UserFactory.create(username='student', password='password')
        self.client.login(username=student.username, password='password')

        post_data = [
            self.student_enrollment('enrolled')
        ]
        url = reverse('programs_api:v1:program_enrollments', args=[uuid4()])
        response = self.client.post(
            url,
            json.dumps(post_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_program_not_found(self):
        post_data = [
            self.student_enrollment('enrolled')
        ]
        url = reverse('programs_api:v1:program_enrollments', args=[uuid4()])
        response = self.client.post(
            url,
            json.dumps(post_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_partially_valid_enrollment(self):

        post_data = [
            self.student_enrollment('new', '001'),
            self.student_enrollment('pending', '003'),
        ]

        url = reverse('programs_api:v1:program_enrollments', args=[uuid4()])
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            with mock.patch(
                'lms.djangoapps.program_enrollments.api.v1.views.get_user_by_program_id',
                autospec=True,
                return_value=None
            ):
                response = self.client.post(url, json.dumps(post_data), content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data, {
            '001': 'invalid-status',
            '003': 'pending',
        })


class ProgramEnrollmentViewPatchTests(APITestCase):
    """
    Tests for the ProgramEnrollment view PATCH method.
    """
    def setUp(self):
        super(ProgramEnrollmentViewPatchTests, self).setUp()

        self.program_uuid = '00000000-1111-2222-3333-444444444444'
        self.curriculum_uuid = 'aaaaaaaa-1111-2222-3333-444444444444'
        self.other_curriculum_uuid = 'bbbbbbbb-1111-2222-3333-444444444444'

        self.course_id = CourseKey.from_string('course-v1:edX+ToyX+Toy_Course')
        _ = CourseOverviewFactory.create(id=self.course_id)

        self.password = 'password'
        self.student = UserFactory.create(username='student', password=self.password)
        self.global_staff = GlobalStaffFactory.create(username='global-staff', password=self.password)

        self.client.login(username=self.global_staff.username, password=self.password)

    def student_enrollment(self, enrollment_status, external_user_key=None):
        return {
            'status': enrollment_status,
            REQUEST_STUDENT_KEY: external_user_key or str(uuid4().hex[0:10]),
        }

    def test_successfully_patched_program_enrollment(self):
        enrollments = {}
        for i in range(4):
            user_key = 'user-{}'.format(i)
            instance = ProgramEnrollment.objects.create(
                program_uuid=self.program_uuid,
                curriculum_uuid=self.curriculum_uuid,
                user=None,
                status='pending',
                external_user_key=user_key,
            )
            enrollments[user_key] = instance

        post_data = [
            {REQUEST_STUDENT_KEY: 'user-1', 'status': 'withdrawn'},
            {REQUEST_STUDENT_KEY: 'user-2', 'status': 'suspended'},
            {REQUEST_STUDENT_KEY: 'user-3', 'status': 'enrolled'},
        ]

        url = reverse('programs_api:v1:program_enrollments', args=[self.program_uuid])
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.client.patch(url, json.dumps(post_data), content_type='application/json')

        for enrollment in enrollments.values():
            enrollment.refresh_from_db()

        expected_statuses = {
            'user-0': 'pending',
            'user-1': 'withdrawn',
            'user-2': 'suspended',
            'user-3': 'enrolled',
        }
        for user_key, enrollment in enrollments.items():
            assert expected_statuses[user_key] == enrollment.status

        expected_response = {
            'user-1': 'withdrawn',
            'user-2': 'suspended',
            'user-3': 'enrolled',
        }
        assert status.HTTP_200_OK == response.status_code
        assert expected_response == response.data

    def test_enrollment_payload_limit(self):
        patch_data = []
        for _ in range(MAX_ENROLLMENT_RECORDS + 1):
            patch_data += self.student_enrollment('enrolled')

        url = reverse('programs_api:v1:program_enrollments', args=[uuid4()])
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.client.patch(url, json.dumps(patch_data), content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    def test_unauthenticated(self):
        self.client.logout()
        patch_data = [
            self.student_enrollment('enrolled')
        ]
        url = reverse('programs_api:v1:program_enrollments', args=[uuid4()])
        response = self.client.patch(
            url,
            json.dumps(patch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_program_unauthorized(self):
        self.client.login(username=self.student.username, password=self.password)

        patch_data = [
            self.student_enrollment('enrolled')
        ]
        url = reverse('programs_api:v1:program_enrollments', args=[uuid4()])
        response = self.client.patch(
            url,
            json.dumps(patch_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_program_not_found(self):
        patch_data = [
            self.student_enrollment('enrolled')
        ]
        url = reverse('programs_api:v1:program_enrollments', args=[uuid4()])
        response = self.client.patch(
            url,
            json.dumps(patch_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unprocessable_enrollment(self):
        url = reverse('programs_api:v1:program_enrollments', args=[uuid4()])

        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.client.patch(
                url,
                json.dumps([{'status': 'enrolled'}]),
                content_type='application/json'
            )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_duplicate_enrollment(self):
        enrollments = {}
        for i in range(4):
            user_key = 'user-{}'.format(i)
            instance = ProgramEnrollment.objects.create(
                program_uuid=self.program_uuid,
                curriculum_uuid=self.curriculum_uuid,
                user=None,
                status='pending',
                external_user_key=user_key,
            )
            enrollments[user_key] = instance

        patch_data = [
            self.student_enrollment('enrolled', 'user-1'),
            self.student_enrollment('enrolled', 'user-2'),
            self.student_enrollment('enrolled', 'user-1'),
        ]

        url = reverse('programs_api:v1:program_enrollments', args=[self.program_uuid])
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.client.patch(url, json.dumps(patch_data), content_type='application/json')

        for enrollment in enrollments.values():
            enrollment.refresh_from_db()

        expected_statuses = {
            'user-0': 'pending',
            'user-1': 'pending',
            'user-2': 'enrolled',
            'user-3': 'pending',
        }
        for user_key, enrollment in enrollments.items():
            assert expected_statuses[user_key] == enrollment.status

        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data, {
            'user-1': 'duplicated',
            'user-2': 'enrolled',
        })

    def test_partially_valid_enrollment(self):
        enrollments = {}
        for i in range(4):
            user_key = 'user-{}'.format(i)
            instance = ProgramEnrollment.objects.create(
                program_uuid=self.program_uuid,
                curriculum_uuid=self.curriculum_uuid,
                user=None,
                status='pending',
                external_user_key=user_key,
            )
            enrollments[user_key] = instance

        patch_data = [
            self.student_enrollment('new', 'user-1'),
            self.student_enrollment('withdrawn', 'user-3'),
            self.student_enrollment('enrolled', 'user-who-is-not-in-program'),
        ]

        url = reverse('programs_api:v1:program_enrollments', args=[self.program_uuid])
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.client.patch(url, json.dumps(patch_data), content_type='application/json')

        for enrollment in enrollments.values():
            enrollment.refresh_from_db()

        expected_statuses = {
            'user-0': 'pending',
            'user-1': 'pending',
            'user-2': 'pending',
            'user-3': 'withdrawn',
        }
        for user_key, enrollment in enrollments.items():
            assert expected_statuses[user_key] == enrollment.status

        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data, {
            'user-1': 'invalid-status',
            'user-3': 'withdrawn',
            'user-who-is-not-in-program': 'not-in-program',
        })
