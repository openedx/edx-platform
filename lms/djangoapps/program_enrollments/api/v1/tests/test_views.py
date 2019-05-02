"""
Unit tests for ProgramEnrollment views.
"""
from __future__ import unicode_literals
from uuid import uuid4
import mock

import ddt
from django.core.cache import cache
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.test import APITestCase
from six import text_type

from lms.djangoapps.courseware.tests.factories import GlobalStaffFactory
from lms.djangoapps.program_enrollments.api.v1.constants import CourseEnrollmentResponseStatuses as CourseStatuses
from lms.djangoapps.program_enrollments.models import ProgramEnrollment, ProgramCourseEnrollment
from student.tests.factories import UserFactory
from openedx.core.djangoapps.catalog.tests.factories import (
    CourseFactory,
    OrganizationFactory as CatalogOrganizationFactory,
    ProgramFactory,
)
from openedx.core.djangolib.testing.utils import CacheIsolationMixin
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.catalog.cache import PROGRAM_CACHE_KEY_TPL
from .factories import ProgramEnrollmentFactory, ProgramCourseEnrollmentFactory


class ProgramEnrollmentListTest(APITestCase):
    """
    Tests for GET calls to the Program Enrollments API.
    """
    @classmethod
    def setUpClass(cls):
        super(ProgramEnrollmentListTest, cls).setUpClass()
        cls.program_uuid = '00000000-1111-2222-3333-444444444444'
        cls.curriculum_uuid = 'aaaaaaaa-1111-2222-3333-444444444444'
        cls.password = 'password'
        cls.student = UserFactory.create(username='student', password=cls.password)
        cls.global_staff = GlobalStaffFactory.create(username='global-staff', password=cls.password)

    @classmethod
    def tearDownClass(cls):
        super(ProgramEnrollmentListTest, cls).tearDownClass()

    def create_enrollments(self):
        """
        Helper method for creating program enrollment records.
        """
        for i in xrange(2):
            user_key = 'user-{}'.format(i)
            ProgramEnrollmentFactory.create(
                program_uuid=self.program_uuid,
                curriculum_uuid=self.curriculum_uuid,
                user=None,
                status='pending',
                external_user_key=user_key,
            )

        for i in xrange(2, 4):
            user_key = 'user-{}'.format(i)
            ProgramEnrollmentFactory.create(
                program_uuid=self.program_uuid, curriculum_uuid=self.curriculum_uuid, external_user_key=user_key,
            )

        self.addCleanup(self.destroy_enrollments)

    def destroy_enrollments(self):
        """
        Deletes program enrollments associated with this test case's program_uuid.
        """
        ProgramEnrollment.objects.filter(program_uuid=self.program_uuid).delete()

    def get_url(self, program_key=None):
        return reverse('programs_api:v1:program_enrollments', kwargs={'program_key': program_key})

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

        self.create_enrollments()
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

        self.create_enrollments()
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
class CourseEnrollmentPostTests(APITestCase, ProgramCacheTestCaseMixin):
    """ Tests for mock course enrollment """

    @classmethod
    def setUpClass(cls):
        super(CourseEnrollmentPostTests, cls).setUpClass()
        cls.start_cache_isolation()
        cls.password = 'password'
        cls.student = UserFactory.create(username='student', password=cls.password)
        cls.global_staff = GlobalStaffFactory.create(username='global-staff', password=cls.password)

    @classmethod
    def tearDownClass(cls):
        cls.end_cache_isolation()
        super(CourseEnrollmentPostTests, cls).tearDownClass()

    def setUp(self):
        super(CourseEnrollmentPostTests, self).setUp()
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

    def test_enrollments(self):
        self.create_program_enrollment('l1')
        self.create_program_enrollment('l2')
        self.create_program_enrollment('l3', user=None)
        self.create_program_enrollment('l4', user=None)
        post_data = [
            self.learner_enrollment("l1", "active"),
            self.learner_enrollment("l2", "inactive"),
            self.learner_enrollment("l3", "active"),
            self.learner_enrollment("l4", "inactive"),
        ]
        response = self.client.post(self.default_url, post_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertDictEqual(
            {
                "l1": "active",
                "l2": "inactive",
                "l3": "active",
                "l4": "inactive",
            },
            response.data
        )
        self.assert_program_course_enrollment("l1", "active", True)
        self.assert_program_course_enrollment("l2", "inactive", True)
        self.assert_program_course_enrollment("l3", "active", False)
        self.assert_program_course_enrollment("l4", "inactive", False)

    def assert_program_course_enrollment(self, external_user_key, expected_status, has_user):
        """
        Convenience method to assert that a ProgramCourseEnrollment has been created,
        and potentially that a CourseEnrollment has also been created
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

    def test_duplicate(self):
        post_data = [
            self.learner_enrollment("l1", "active"),
            self.learner_enrollment("l1", "active"),
        ]
        response = self.client.post(self.default_url, post_data, format="json")
        self.assertEqual(422, response.status_code)
        self.assertDictEqual(
            {
                "l1": CourseStatuses.DUPLICATED
            },
            response.data
        )

    def test_conflict(self):
        program_enrollment = self.create_program_enrollment('l1')
        ProgramCourseEnrollmentFactory.create(
            program_enrollment=program_enrollment,
            course_key=self.course_key
        )
        post_data = [self.learner_enrollment("l1")]
        response = self.client.post(self.default_url, post_data, format="json")
        self.assertEqual(422, response.status_code)
        self.assertDictEqual({'l1': CourseStatuses.CONFLICT}, response.data)

    def test_user_not_in_program(self):
        self.create_program_enrollment('l1')
        post_data = [
            self.learner_enrollment("l1"),
            self.learner_enrollment("l2"),
        ]
        response = self.client.post(self.default_url, post_data, format="json")
        self.assertEqual(207, response.status_code)
        self.assertDictEqual(
            {
                "l1": "active",
                "l2": "not-in-program",
            },
            response.data
        )

    def test_401_not_logged_in(self):
        self.client.logout()
        post_data = [self.learner_enrollment("A")]
        response = self.client.post(self.default_url, post_data, format="json")
        self.assertEqual(401, response.status_code)

    def test_403_forbidden(self):
        self.client.logout()
        self.client.login(username=self.student, password=self.password)
        post_data = [self.learner_enrollment("A")]
        response = self.client.post(self.default_url, post_data, format="json")
        self.assertEqual(403, response.status_code)

    def test_413_payload_too_large(self):
        post_data = [self.learner_enrollment(str(i)) for i in range(30)]
        response = self.client.post(self.default_url, post_data, format="json")
        self.assertEqual(413, response.status_code)

    def test_404_not_found_program(self):
        paths = [
            self.get_url(uuid4(), self.course_key),
            self.get_url(self.program_uuid, CourseKey.from_string("course-v1:fake+fake+fake")),
            self.get_url(self.program_uuid, self.course_not_in_program_key),
        ]
        post_data = [self.learner_enrollment("A")]
        for path_404 in paths:
            response = self.client.post(path_404, post_data, format="json")
            self.assertEqual(404, response.status_code)

    def test_invalid_status(self):
        post_data = [self.learner_enrollment('A', 'this-is-not-a-status')]
        response = self.client.post(self.default_url, post_data, format="json")
        self.assertEqual(422, response.status_code)
        self.assertDictEqual({'A': CourseStatuses.INVALID_STATUS}, response.data)

    @ddt.data(
        [{'status': 'active'}],
        [{'student_key': '000'}],
        ["this isn't even a dict!"],
        [{'student_key': '000', 'status': 'active'}, "bad_data"],
        "not a list",
    )
    def test_422_unprocessable_entity_bad_data(self, post_data):
        response = self.client.post(self.default_url, post_data, format="json")
        self.assertEqual(response.status_code, 422)
        self.assertIn('invalid enrollment record', response.data)
