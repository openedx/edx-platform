"""
Unit tests for ProgramEnrollment views.
"""
from __future__ import absolute_import, unicode_literals

import json
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import ddt
import mock
from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from freezegun import freeze_time
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from rest_framework import status
from rest_framework.test import APITestCase
from six import text_type
from six.moves import range, zip

from bulk_email.models import BulkEmailFlag, Optout
from course_modes.models import CourseMode
from lms.djangoapps.certificates.models import CertificateStatuses
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from lms.djangoapps.courseware.tests.factories import GlobalStaffFactory, InstructorFactory
from lms.djangoapps.program_enrollments.api.v1.constants import MAX_ENROLLMENT_RECORDS, REQUEST_STUDENT_KEY
from lms.djangoapps.program_enrollments.api.v1.constants import CourseEnrollmentResponseStatuses as CourseStatuses
from lms.djangoapps.program_enrollments.api.v1.constants import CourseRunProgressStatuses
from lms.djangoapps.program_enrollments.api.v1.constants import ProgramEnrollmentResponseStatuses as ProgramStatuses
from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment, ProgramEnrollment
from lms.djangoapps.program_enrollments.tests.factories import ProgramCourseEnrollmentFactory, ProgramEnrollmentFactory
from lms.djangoapps.program_enrollments.utils import ProviderDoesNotExistException
from openedx.core.djangoapps.catalog.cache import PROGRAM_CACHE_KEY_TPL
from openedx.core.djangoapps.catalog.tests.factories import CourseFactory, CourseRunFactory
from openedx.core.djangoapps.catalog.tests.factories import OrganizationFactory as CatalogOrganizationFactory
from openedx.core.djangoapps.catalog.tests.factories import ProgramFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangolib.testing.utils import CacheIsolationMixin
from student.roles import CourseStaffRole
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory as ModulestoreCourseFactory
from xmodule.modulestore.tests.factories import ItemFactory


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
        cls.program_uuid_tmpl = '00000000-1111-2222-3333-4444444444{0:02d}'
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


@ddt.ddt
class UserProgramReadOnlyAccessViewTest(ListViewTestMixin, APITestCase):
    """
    Tests for the UserProgramReadonlyAccess view class
    """
    view_name = 'programs_api:v1:user_program_readonly_access'

    @classmethod
    def setUpClass(cls):
        super(UserProgramReadOnlyAccessViewTest, cls).setUpClass()

        cls.mock_program_data = [
            {'uuid': cls.program_uuid_tmpl.format(11), 'marketing_slug': 'garbage-program', 'type': 'masters'},
            {'uuid': cls.program_uuid_tmpl.format(22), 'marketing_slug': 'garbage-study', 'type': 'micromaster'},
            {'uuid': cls.program_uuid_tmpl.format(33), 'marketing_slug': 'garbage-life', 'type': 'masters'},
        ]

        cls.course_staff = InstructorFactory.create(password=cls.password, course_key=cls.course_id)
        cls.date = datetime(2013, 1, 22, tzinfo=UTC)
        CourseEnrollmentFactory(
            course_id=cls.course_id,
            user=cls.course_staff,
            created=cls.date,
        )

    def test_401_if_anonymous(self):
        response = self.client.get(reverse(self.view_name))
        assert status.HTTP_401_UNAUTHORIZED == response.status_code

    @ddt.data(
        ('masters', 2),
        ('micromaster', 1)
    )
    @ddt.unpack
    def test_global_staff(self, program_type, expected_data_size):
        self.client.login(username=self.global_staff.username, password=self.password)
        mock_return_value = [program for program in self.mock_program_data if program['type'] == program_type]

        with mock.patch(
            'lms.djangoapps.program_enrollments.api.v1.views.get_programs_by_type',
            autospec=True,
            return_value=mock_return_value
        ) as mock_get_programs_by_type:
            response = self.client.get(reverse(self.view_name) + '?type=' + program_type)

        assert status.HTTP_200_OK == response.status_code
        assert len(response.data) == expected_data_size
        mock_get_programs_by_type.assert_called_once_with(response.wsgi_request.site, program_type)

    def test_course_staff(self):
        self.client.login(username=self.course_staff.username, password=self.password)

        with mock.patch(
            'lms.djangoapps.program_enrollments.api.v1.views.get_programs',
            autospec=True,
            return_value=[self.mock_program_data[0]]
        ) as mock_get_programs:
            response = self.client.get(reverse(self.view_name) + '?type=masters')

        assert status.HTTP_200_OK == response.status_code
        assert len(response.data) == 1
        mock_get_programs.assert_called_once_with(course=self.course_id)

    def test_course_staff_of_multiple_courses(self):
        other_course_key = CourseKey.from_string('course-v1:edX+ToyX+Other_Course')

        CourseEnrollmentFactory.create(course_id=other_course_key, user=self.course_staff)
        CourseStaffRole(other_course_key).add_users(self.course_staff)

        self.client.login(username=self.course_staff.username, password=self.password)

        with mock.patch(
            'lms.djangoapps.program_enrollments.api.v1.views.get_programs',
            autospec=True,
            side_effect=[[self.mock_program_data[0]], [self.mock_program_data[2]]]
        ) as mock_get_programs:
            response = self.client.get(reverse(self.view_name) + '?type=masters')

        assert status.HTTP_200_OK == response.status_code
        assert len(response.data) == 2
        mock_get_programs.assert_has_calls([
            mock.call(course=self.course_id),
            mock.call(course=other_course_key),
        ])

    @mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True, return_value=None)
    def test_learner_200_if_no_programs_enrolled(self, mock_get_programs):
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.get(reverse(self.view_name))

        assert status.HTTP_200_OK == response.status_code
        assert response.data == []
        mock_get_programs.assert_called_once_with(uuids=[])

    def test_learner_200_many_programs(self):
        for program in self.mock_program_data:
            ProgramEnrollmentFactory.create(
                program_uuid=program['uuid'],
                curriculum_uuid=self.curriculum_uuid,
                user=self.student,
                status='pending',
                external_user_key='user-{}'.format(self.student.id),
            )
        self.client.login(username=self.student.username, password=self.password)

        with mock.patch(
            'lms.djangoapps.program_enrollments.api.v1.views.get_programs',
            autospec=True,
            return_value=self.mock_program_data
        ) as mock_get_programs:
            response = self.client.get(reverse(self.view_name))

        assert status.HTTP_200_OK == response.status_code
        assert len(response.data) == 3
        mock_get_programs.assert_called_once_with(uuids=[UUID(item['uuid']) for item in self.mock_program_data])


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
        self.set_program_in_catalog_cache(program_uuid, program)
        return program

    def set_program_in_catalog_cache(self, program_uuid, program):
        cache.set(PROGRAM_CACHE_KEY_TPL.format(uuid=program_uuid), program, None)


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
        curriculum = next(c for c in self.program['curricula'] if c['is_active'])
        self.course = curriculum['courses'][0]
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

    def prepare_student(self, key):
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
                mode=CourseMode.MASTERS
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

    def assert_program_course_enrollment(self, external_user_key, expected_status, has_user, mode=CourseMode.MASTERS):
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
            self.assertEqual(mode, course_enrollment.mode)
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

    def test_404_no_curriculum(self):
        self.program['curricula'] = []
        self.set_program_in_catalog_cache(self.program_uuid, self.program)
        request_data = [self.learner_enrollment("learner-1")]
        response = self.request(self.default_url, request_data)
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
        self.assertEqual(response.status_code, 400)
        self.assertIn('invalid enrollment record', response.data)

    @ddt.data(
        [{'status': 'pending'}],
        [{'status': 'not-a-status'}],
        [{'status': 'pending'}, {'status': 'pending'}],
    )
    def test_no_student_key(self, bad_records):
        request_data = [self.learner_enrollment('learner-1')]
        request_data.extend(bad_records)
        response = self.request(self.default_url, request_data)

        self.assertEqual(response.status_code, 400)
        self.assertIn('invalid enrollment record', response.data)

    def test_extra_field(self):
        self.prepare_student('learner-1')
        enrollment = self.learner_enrollment('learner-1', 'inactive')
        enrollment['favorite_author'] = 'Hemingway'
        request_data = [enrollment]
        response = self.request(self.default_url, request_data)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.data,
            {'learner-1': 'inactive'}
        )


class CourseEnrollmentPostTests(BaseCourseEnrollmentTestsMixin, APITestCase):
    """ Tests for course enrollment POST """

    def request(self, path, data):
        return self.client.post(path, data, format='json')

    def prepare_student(self, key):
        self.create_program_enrollment(key)

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

    def test_program_course_enrollment_exists(self):
        """
        The program enrollments application already has a program_course_enrollment
        record for this user and course
        """
        self.create_program_and_course_enrollments('learner-1')
        post_data = [self.learner_enrollment("learner-1")]
        response = self.request(self.default_url, post_data)
        self.assertEqual(422, response.status_code)
        self.assertDictEqual({'learner-1': CourseStatuses.CONFLICT}, response.data)

    def test_user_currently_enrolled_in_course(self):
        """
        If a user is already enrolled in a course through a different method
        that enrollment should be linked but not overwritten as masters.
        """
        CourseEnrollmentFactory.create(
            course_id=self.course_key,
            user=self.student,
            mode=CourseMode.VERIFIED
        )

        self.create_program_enrollment('learner-1', user=self.student)

        post_data = [
            self.learner_enrollment("learner-1", "active")
        ]
        response = self.request(self.default_url, post_data)

        self.assertEqual(200, response.status_code)
        self.assertDictEqual(
            {
                "learner-1": "active"
            },
            response.data
        )
        self.assert_program_course_enrollment("learner-1", "active", True, mode=CourseMode.VERIFIED)

    def test_207_multistatus(self):
        self.create_program_enrollment('learner-1')
        post_data = [self.learner_enrollment("learner-1"), self.learner_enrollment("learner-2")]
        response = self.request(self.default_url, post_data)
        self.assertEqual(207, response.status_code)
        self.assertDictEqual(
            {'learner-1': CourseStatuses.ACTIVE, 'learner-2': CourseStatuses.NOT_IN_PROGRAM},
            response.data
        )


# pylint: disable=no-member
@ddt.ddt
class CourseEnrollmentModificationTestBase(BaseCourseEnrollmentTestsMixin):
    """
    Base class for both the PATCH and PUT endpoints for Course Enrollment API
    Children needs to implement assert_user_not_enrolled_test_result and
    setup_change_test_data
    """

    def prepare_student(self, key):
        self.create_program_and_course_enrollments(key)

    def test_207_multistatus(self):
        self.create_program_and_course_enrollments('learner-1')
        mod_data = [self.learner_enrollment("learner-1"), self.learner_enrollment("learner-2")]
        response = self.request(self.default_url, mod_data)
        self.assertEqual(207, response.status_code)
        self.assertDictEqual(
            {'learner-1': CourseStatuses.ACTIVE, 'learner-2': CourseStatuses.NOT_IN_PROGRAM},
            response.data
        )

    def test_user_not_enrolled_in_course(self):
        self.create_program_enrollment('learner-1')
        patch_data = [self.learner_enrollment('learner-1')]
        response = self.request(self.default_url, patch_data)
        self.assert_user_not_enrolled_test_result(response)

    def assert_user_not_enrolled_test_result(self, response):
        pass

    def setup_change_test_data(self, initial_statuses):
        pass

    @ddt.data(
        ('active', 'inactive', 'active', 'inactive'),
        ('inactive', 'active', 'inactive', 'active'),
        ('active', 'active', 'active', 'active'),
        ('inactive', 'inactive', 'inactive', 'inactive'),
    )
    def test_change_status(self, initial_statuses):
        self.setup_change_test_data(initial_statuses)
        mod_data = [
            self.learner_enrollment('learner-1', 'inactive'),
            self.learner_enrollment('learner-2', 'active'),
            self.learner_enrollment('learner-3', 'inactive'),
            self.learner_enrollment('learner-4', 'active'),
        ]
        response = self.request(self.default_url, mod_data)
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


class CourseEnrollmentPatchTests(CourseEnrollmentModificationTestBase, APITestCase):
    """ Tests for course enrollment PATCH """

    def request(self, path, data):
        return self.client.patch(path, data, format='json')

    def assert_user_not_enrolled_test_result(self, response):
        self.assertEqual(422, response.status_code)
        self.assertDictEqual({'learner-1': CourseStatuses.NOT_FOUND}, response.data)

    def setup_change_test_data(self, initial_statuses):
        self.create_program_and_course_enrollments('learner-1', course_status=initial_statuses[0])
        self.create_program_and_course_enrollments('learner-2', course_status=initial_statuses[1])
        self.create_program_and_course_enrollments('learner-3', course_status=initial_statuses[2], user=None)
        self.create_program_and_course_enrollments('learner-4', course_status=initial_statuses[3], user=None)


class CourseEnrollmentPutTests(CourseEnrollmentModificationTestBase, APITestCase):
    """ Tests for course enrollment PUT """

    def request(self, path, data):
        return self.client.put(path, data, format='json')

    def assert_user_not_enrolled_test_result(self, response):
        self.assertEqual(200, response.status_code)
        self.assertDictEqual({'learner-1': CourseStatuses.ACTIVE}, response.data)

    def setup_change_test_data(self, initial_statuses):
        self.create_program_and_course_enrollments('learner-1', course_status=initial_statuses[0])
        self.create_program_enrollment('learner-2')
        self.create_program_enrollment('learner-3', user=None)
        self.create_program_and_course_enrollments('learner-4', course_status=initial_statuses[3], user=None)


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


@ddt.ddt
class BaseProgramEnrollmentWriteTestsMixin(object):
    """ Mixin class that defines common tests for program enrollment write endpoints """
    add_uuid = False
    program_uuid = '00000000-1111-2222-3333-444444444444'
    success_status = 200

    def student_enrollment(self, enrollment_status, external_user_key=None, prepare_student=False):
        """ Convenience method to create a student enrollment record """
        enrollment = {
            REQUEST_STUDENT_KEY: external_user_key or str(uuid4().hex[0:10]),
            'status': enrollment_status,
        }
        if self.add_uuid:
            enrollment['curriculum_uuid'] = str(uuid4())
        if prepare_student:
            self.prepare_student(enrollment)
        return enrollment

    def prepare_student(self, enrollment):
        pass

    def get_url(self, program_uuid=None):
        if program_uuid is None:
            program_uuid = uuid4()
        return reverse('programs_api:v1:program_enrollments', args=[program_uuid])

    def test_unauthenticated(self):
        self.client.logout()
        request_data = [self.student_enrollment('enrolled')]
        response = self.request(self.get_url(), json.dumps(request_data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_enrollment_payload_limit(self):
        request_data = [self.student_enrollment('enrolled') for _ in range(MAX_ENROLLMENT_RECORDS + 1)]
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.request(self.get_url(), json.dumps(request_data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    def test_duplicate_enrollment(self):
        request_data = [
            self.student_enrollment('enrolled', '001'),
            self.student_enrollment('enrolled', '001'),
        ]

        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.request(self.get_url(), json.dumps(request_data), content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data, {'001': 'duplicated'})

    def test_unprocessable_enrollment(self):
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.request(
                self.get_url(),
                json.dumps([{'status': 'enrolled'}]),
                content_type='application/json'
            )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data, 'invalid enrollment record')

    def test_program_unauthorized(self):
        student = UserFactory.create(password='password')
        self.client.login(username=student.username, password='password')

        request_data = [self.student_enrollment('enrolled')]
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.request(self.get_url(), json.dumps(request_data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_program_not_found(self):
        post_data = [self.student_enrollment('enrolled')]
        nonexistant_uuid = uuid4()
        response = self.request(
            self.get_url(program_uuid=nonexistant_uuid),
            json.dumps(post_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @ddt.data(
        [{'status': 'pending'}],
        [{'status': 'not-a-status'}],
        [{'status': 'pending'}, {'status': 'pending'}],
    )
    def test_no_student_key(self, bad_records):
        program_uuid = uuid4()
        url = reverse('programs_api:v1:program_enrollments', args=[program_uuid])
        enrollments = [self.student_enrollment('enrolled', '001', True)]
        enrollments.extend(bad_records)

        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.request(url, json.dumps(enrollments), content_type='application/json')

        self.assertEqual(422, response.status_code)
        self.assertEqual('invalid enrollment record', response.data)

    def test_extra_field(self):
        self.student_enrollment('pending', 'learner-01', prepare_student=True)
        enrollment = self.student_enrollment('enrolled', 'learner-01')
        enrollment['favorite_pokemon'] = 'bulbasaur'
        enrollments = [enrollment]
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            with mock.patch(
                'lms.djangoapps.program_enrollments.api.v1.views.get_user_by_program_id',
                autospec=True,
                return_value=None
            ):
                url = self.get_url(program_uuid=self.program_uuid)
                response = self.request(url, json.dumps(enrollments), content_type='application/json')
        self.assertEqual(self.success_status, response.status_code)
        self.assertDictEqual(
            response.data,
            {'learner-01': 'enrolled'}
        )


@ddt.ddt
class ProgramEnrollmentViewPostTests(BaseProgramEnrollmentWriteTestsMixin, APITestCase):
    """
    Tests for the ProgramEnrollment view POST method.
    """
    add_uuid = True
    success_status = status.HTTP_201_CREATED
    success_status = 201

    def setUp(self):
        super(ProgramEnrollmentViewPostTests, self).setUp()
        self.request = self.client.post
        global_staff = GlobalStaffFactory.create(username='global-staff', password='password')
        self.client.login(username=global_staff.username, password='password')

    def tearDown(self):
        super(ProgramEnrollmentViewPostTests, self).tearDown()
        ProgramEnrollment.objects.all().delete()

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

    def test_program_enrollments_no_idp(self):
        program_key = uuid4()
        curriculum_uuid = uuid4()

        post_data = [
            {
                'status': 'enrolled',
                REQUEST_STUDENT_KEY: 'abc{}'.format(i),
                'curriculum_uuid': str(curriculum_uuid)
            } for i in range(3)
        ]

        url = reverse('programs_api:v1:program_enrollments', args=[program_key])

        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            with mock.patch(
                'lms.djangoapps.program_enrollments.api.v1.views.get_user_by_program_id',
                autospec=True,
                side_effect=ProviderDoesNotExistException()
            ):
                response = self.client.post(url, json.dumps(post_data), content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for i in range(3):
            enrollment = ProgramEnrollment.objects.get(external_user_key='abc{}'.format(i))

            self.assertEqual(enrollment.program_uuid, program_key)
            self.assertEqual(enrollment.status, 'enrolled')
            self.assertEqual(enrollment.curriculum_uuid, curriculum_uuid)
            self.assertIsNone(enrollment.user)


@ddt.ddt
class ProgramEnrollmentViewPatchTests(BaseProgramEnrollmentWriteTestsMixin, APITestCase):
    """
    Tests for the ProgramEnrollment view PATCH method.
    """
    add_uuid = False
    success_status = status.HTTP_200_OK

    def setUp(self):
        super(ProgramEnrollmentViewPatchTests, self).setUp()
        self.request = self.client.patch

        self.curriculum_uuid = 'aaaaaaaa-1111-2222-3333-444444444444'
        self.other_curriculum_uuid = 'bbbbbbbb-1111-2222-3333-444444444444'

        self.course_id = CourseKey.from_string('course-v1:edX+ToyX+Toy_Course')
        _ = CourseOverviewFactory.create(id=self.course_id)

        self.password = 'password'
        self.student = UserFactory.create(username='student', password=self.password)
        self.global_staff = GlobalStaffFactory.create(username='global-staff', password=self.password)

        self.client.login(username=self.global_staff.username, password=self.password)

    def prepare_student(self, enrollment):
        ProgramEnrollment.objects.create(
            program_uuid=self.program_uuid,
            curriculum_uuid=self.curriculum_uuid,
            user=None,
            status='pending',
            external_user_key=enrollment[REQUEST_STUDENT_KEY],
        )

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
            {REQUEST_STUDENT_KEY: 'user-1', 'status': 'canceled'},
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
            'user-1': 'canceled',
            'user-2': 'suspended',
            'user-3': 'enrolled',
        }
        for user_key, enrollment in enrollments.items():
            assert expected_statuses[user_key] == enrollment.status

        expected_response = {
            'user-1': 'canceled',
            'user-2': 'suspended',
            'user-3': 'enrolled',
        }
        assert status.HTTP_200_OK == response.status_code
        assert expected_response == response.data

    def test_duplicate_enrollment_record_changed(self):
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

    def test_partially_valid_enrollment_record_changed(self):
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
            self.student_enrollment('canceled', 'user-3'),
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
            'user-3': 'canceled',
        }
        for user_key, enrollment in enrollments.items():
            assert expected_statuses[user_key] == enrollment.status

        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data, {
            'user-1': 'invalid-status',
            'user-3': 'canceled',
            'user-who-is-not-in-program': 'not-in-program',
        })


@ddt.ddt
class ProgramEnrollmentViewPutTests(BaseProgramEnrollmentWriteTestsMixin, APITestCase):
    """
    Tests for the ProgramEnrollment view PATCH method.
    """
    add_uuid = True
    success_status = status.HTTP_200_OK

    def setUp(self):
        super(ProgramEnrollmentViewPutTests, self).setUp()
        self.request = self.client.put

        self.program_uuid = '00000000-1111-2222-3333-444444444444'
        self.curriculum_uuid = 'aaaaaaaa-1111-2222-3333-444444444444'

        self.global_staff = GlobalStaffFactory.create(username='global-staff', password='password')
        self.client.login(username=self.global_staff.username, password='password')

        patch_get_user = mock.patch(
            'lms.djangoapps.program_enrollments.api.v1.views.get_user_by_program_id',
            autospec=True,
            return_value=None
        )
        self.mock_get_user = patch_get_user.start()
        self.addCleanup(patch_get_user.stop)

    def prepare_student(self, enrollment):
        ProgramEnrollment.objects.create(
            program_uuid=self.program_uuid,
            curriculum_uuid=self.curriculum_uuid,
            user=None,
            status='pending',
            external_user_key=enrollment[REQUEST_STUDENT_KEY],
        )

    @ddt.data(True, False)
    def test_all_create_or_modify(self, create_users):
        request_data = [
            self.student_enrollment(ProgramStatuses.ENROLLED)
            for _ in range(5)
        ]
        if create_users:
            for enrollment in request_data:
                ProgramEnrollmentFactory(
                    program_uuid=self.program_uuid,
                    status=ProgramStatuses.PENDING,
                    external_user_key=enrollment[REQUEST_STUDENT_KEY],
                )

        url = self.get_url(program_uuid=self.program_uuid)
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.client.put(url, json.dumps(request_data), content_type='application/json')
        self.assertEqual(self.success_status, response.status_code)
        self.assertEqual(5, len(response.data))
        for response_status in response.data.values():
            self.assertEqual(response_status, ProgramStatuses.ENROLLED)

    def test_half_create_modify(self):
        request_data = [
            self.student_enrollment(ProgramStatuses.ENROLLED, 'learner-01'),
            self.student_enrollment(ProgramStatuses.ENROLLED, 'learner-02'),
            self.student_enrollment(ProgramStatuses.ENROLLED, 'learner-03'),
            self.student_enrollment(ProgramStatuses.ENROLLED, 'learner-04'),
        ]
        ProgramEnrollmentFactory(
            program_uuid=self.program_uuid,
            status=ProgramStatuses.PENDING,
            external_user_key='learner-03',
        )
        ProgramEnrollmentFactory(
            program_uuid=self.program_uuid,
            status=ProgramStatuses.PENDING,
            external_user_key='learner-04',
        )

        url = self.get_url(program_uuid=self.program_uuid)
        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_programs', autospec=True):
            response = self.client.put(url, json.dumps(request_data), content_type='application/json')
        self.assertEqual(self.success_status, response.status_code)
        self.assertEqual(4, len(response.data))
        for response_status in response.data.values():
            self.assertEqual(response_status, ProgramStatuses.ENROLLED)


@ddt.ddt
class ProgramCourseEnrollmentOverviewViewTests(ProgramCacheTestCaseMixin, SharedModuleStoreTestCase, APITestCase):
    """
    Tests for the ProgramCourseEnrollmentOverview view GET method.
    """
    @classmethod
    def setUpClass(cls):
        super(ProgramCourseEnrollmentOverviewViewTests, cls).setUpClass()

        cls.program_uuid = '00000000-1111-2222-3333-444444444444'
        cls.curriculum_uuid = 'aaaaaaaa-1111-2222-3333-444444444444'
        cls.other_curriculum_uuid = 'bbbbbbbb-1111-2222-3333-444444444444'

        cls.course_id = CourseKey.from_string('course-v1:edX+ToyX+Toy_Course')
        cls.course_run = CourseRunFactory.create(key=text_type(cls.course_id))
        cls.course = CourseFactory.create(course_runs=[cls.course_run])

        cls.password = 'password'
        cls.student = UserFactory.create(username='student', password=cls.password)

        # only freeze time when defining these values and not on the whole test case
        # as test_multiple_enrollments_all_enrolled relies on actual differences in modified datetimes
        with freeze_time('2019-01-01'):
            cls.yesterday = datetime.utcnow() - timedelta(1)
            cls.tomorrow = datetime.utcnow() + timedelta(1)

        cls.certificate_download_url = 'www.certificates.com'

    def setUp(self):
        super(ProgramCourseEnrollmentOverviewViewTests, self).setUp()

        # create program enrollment
        self.program_enrollment = ProgramEnrollmentFactory.create(
            program_uuid=self.program_uuid,
            curriculum_uuid=self.curriculum_uuid,
            user=self.student,
        )

        # create course enrollment
        self.course_enrollment = CourseEnrollmentFactory.create(
            course_id=self.course_id,
            user=self.student,
            mode=CourseMode.MASTERS,
        )

        # create course overview
        self.course_overview = CourseOverviewFactory.create(
            id=self.course_id,
            start=self.yesterday,
            end=self.tomorrow,
        )

        # create program course enrollment
        self.program_course_enrollment = ProgramCourseEnrollmentFactory.create(
            program_enrollment=self.program_enrollment,
            course_enrollment=self.course_enrollment,
            course_key=self.course_id,
            status='active',
        )

        # create program
        self.program = self.setup_catalog_cache(self.program_uuid, 'organization_key')
        self.program['curricula'][0]['courses'].append(self.course)
        self.set_program_in_catalog_cache(self.program_uuid, self.program)

    def create_generated_certificate(self):
        return GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course_id,
            status=CertificateStatuses.downloadable,
            mode='verified',
            download_url=self.certificate_download_url,
            grade="0.88",
            verify_uuid=uuid4(),
        )

    def get_url(self, program_uuid=None):
        """ Returns the primary URL requested by the test case. """
        kwargs = {'program_uuid': program_uuid or self.program_uuid}

        return reverse('programs_api:v1:program_course_enrollments_overview', kwargs=kwargs)

    def test_401_if_anonymous(self):
        response = self.client.get(self.get_url(self.program_uuid))
        assert status.HTTP_401_UNAUTHORIZED == response.status_code

    def test_404_if_no_program_with_key(self):
        self.client.login(username=self.student.username, password=self.password)
        self.set_program_in_catalog_cache(self.program_uuid, None)

        response = self.client.get(self.get_url(self.program_uuid))
        assert status.HTTP_404_NOT_FOUND == response.status_code

    def test_403_if_not_enrolled_in_program(self):
        # delete program enrollment
        ProgramEnrollment.objects.all().delete()
        self.client.login(username=self.student.username, password=self.password)
        response = self.client.get(self.get_url(self.program_uuid))
        assert status.HTTP_403_FORBIDDEN == response.status_code

    def _add_new_course_to_program(self, course_run_key, program):
        """
        Helper method to create another course, an overview for it,
        add it to the program, and re-load the cache.
        """
        other_course_run = CourseRunFactory.create(key=text_type(course_run_key))
        other_course = CourseFactory.create(course_runs=[other_course_run])
        program['courses'].append(other_course)
        self.set_program_in_catalog_cache(program['uuid'], program)
        CourseOverviewFactory.create(
            id=course_run_key,
            start=self.yesterday,
        )

    def test_multiple_enrollments_all_enrolled(self):
        other_course_key = CourseKey.from_string('course-v1:edX+ToyX+Other_Course')
        self._add_new_course_to_program(other_course_key, self.program)

        # add a second course enrollment, which doesn't need a ProgramCourseEnrollment
        # to be returned.
        CourseEnrollmentFactory.create(
            course_id=other_course_key,
            user=self.student,
            mode=CourseMode.VERIFIED,
        )

        self.client.login(username=self.student.username, password=self.password)
        response = self.client.get(self.get_url(self.program_uuid))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        actual_course_run_ids = {run['course_run_id'] for run in response.data['course_runs']}
        expected_course_run_ids = {text_type(other_course_key), text_type(self.course_id)}
        self.assertEqual(expected_course_run_ids, actual_course_run_ids)

    @mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_resume_urls_for_enrollments')
    def test_resume_urls(self, mock_get_resume_urls):
        self.client.login(username=self.student.username, password=self.password)

        mock_get_resume_urls.return_value = {self.course_id: ''}
        response = self.client.get(self.get_url(self.program_uuid))
        self.assertNotIn('resume_course_run_url', response.data['course_runs'][0])

        resume_url = 'www.resume.com'
        mock_get_resume_urls.return_value = {self.course_id: resume_url}
        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(resume_url, response.data['course_runs'][0]['resume_course_run_url'])

    def test_no_certificate_available(self):
        self.client.login(username=self.student.username, password=self.password)

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        assert 'certificate_download_url' not in response.data['course_runs'][0]

    def test_certificate_available(self):
        self.client.login(username=self.student.username, password=self.password)
        self.create_generated_certificate()

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(response.data['course_runs'][0]['certificate_download_url'], self.certificate_download_url)

    def test_no_due_dates(self):
        self.client.login(username=self.student.username, password=self.password)

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        assert [] == response.data['course_runs'][0]['due_dates']

    def test_due_dates(self):
        course = ModulestoreCourseFactory.create(
            org="edX",
            course="ToyX",
            run="Toy_Course",
        )
        section_1 = ItemFactory.create(
            category='chapter',
            start=self.yesterday,
            due=self.tomorrow,
            parent=course,
            display_name='section 1'
        )

        subsection_1 = ItemFactory.create(
            category='sequential',
            due=self.tomorrow,
            parent=section_1,
            display_name='subsection 1'
        )

        subsection_2 = ItemFactory.create(
            category='sequential',
            due=self.tomorrow - timedelta(1),
            parent=section_1,
            display_name='subsection 2'
        )

        subsection_3 = ItemFactory.create(
            category='sequential',
            parent=section_1,
            display_name='subsection 3'
        )

        unit_1 = ItemFactory.create(
            category='vertical',
            due=self.tomorrow + timedelta(2),
            parent=subsection_3,
            display_name='unit_1'
        )

        with mock.patch('lms.djangoapps.program_enrollments.api.v1.views.get_dates_for_course') as mock_get_dates:
            mock_get_dates.return_value = {
                (section_1.location, 'due'): section_1.due,
                (section_1.location, 'start'): section_1.start,
                (subsection_1.location, 'due'): subsection_1.due,
                (subsection_2.location, 'due'): subsection_2.due,
                (unit_1.location, 'due'): unit_1.due,
            }

            self.client.login(username=self.student.username, password=self.password)
            response = self.client.get(self.get_url(self.program_uuid))
            self.assertEqual(status.HTTP_200_OK, response.status_code)

            block_data = [
                {
                    'name': section_1.display_name,
                    'url': ('http://testserver/courses/course-v1:edX+ToyX+Toy_Course/'
                            'jump_to/i4x://edX/ToyX/chapter/section_1'),
                    'date': '2019-01-02T00:00:00Z',
                },
                {
                    'name': subsection_1.display_name,
                    'url': ('http://testserver/courses/course-v1:edX+ToyX+Toy_Course/'
                            'jump_to/i4x://edX/ToyX/sequential/subsection_1'),
                    'date': '2019-01-02T00:00:00Z',
                },
                {
                    'name': subsection_2.display_name,
                    'url': ('http://testserver/courses/course-v1:edX+ToyX+Toy_Course/'
                            'jump_to/i4x://edX/ToyX/sequential/subsection_2'),
                    'date': '2019-01-01T00:00:00Z',
                },
                {
                    'name': unit_1.display_name,
                    'url': ('http://testserver/courses/course-v1:edX+ToyX+Toy_Course/'
                            'jump_to/i4x://edX/ToyX/vertical/unit_1'),
                    'date': '2019-01-04T00:00:00Z',
                },
            ]
            due_dates = response.data['course_runs'][0]['due_dates']

            for block in block_data:
                self.assertIn(block, due_dates)

    @mock.patch.object(CourseOverview, 'has_ended')
    def test_course_run_status_instructor_paced_completed(self, mock_has_ended):
        self.client.login(username=self.student.username, password=self.password)

        # set as instructor paced
        self.course_overview.self_paced = False
        self.course_overview.save()

        mock_has_ended.return_value = True

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(CourseRunProgressStatuses.COMPLETED, response.data['course_runs'][0]['course_run_status'])

    @mock.patch.object(CourseOverview, 'has_ended')
    @mock.patch.object(CourseOverview, 'has_started')
    def test_course_run_status_instructor_paced_in_progress(self, mock_has_started, mock_has_ended):
        self.client.login(username=self.student.username, password=self.password)

        # set as instructor paced
        self.course_overview.self_paced = False
        self.course_overview.save()

        mock_has_started.return_value = True
        mock_has_ended.return_value = False

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(CourseRunProgressStatuses.IN_PROGRESS, response.data['course_runs'][0]['course_run_status'])

    @mock.patch.object(CourseOverview, 'has_ended')
    @mock.patch.object(CourseOverview, 'has_started')
    def test_course_run_status_instructor_paced_upcoming(self, mock_has_started, mock_has_ended):
        self.client.login(username=self.student.username, password=self.password)

        # set as instructor paced
        self.course_overview.self_paced = False
        self.course_overview.save()

        mock_has_started.return_value = False
        mock_has_ended.return_value = False

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(CourseRunProgressStatuses.UPCOMING, response.data['course_runs'][0]['course_run_status'])

    @mock.patch.object(CourseOverview, 'has_ended')
    def test_course_run_status_self_paced_completed(self, mock_has_ended):
        self.client.login(username=self.student.username, password=self.password)

        # set as self paced
        self.course_overview.self_paced = True
        self.course_overview.save()

        # course run has ended
        mock_has_ended.return_value = True

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(CourseRunProgressStatuses.COMPLETED, response.data['course_runs'][0]['course_run_status'])

        # course run has not ended and user has earned a passing certificate more than 30 days ago
        certificate = self.create_generated_certificate()
        certificate.created_date = datetime.utcnow() - timedelta(30)
        certificate.save()
        mock_has_ended.return_value = False

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(CourseRunProgressStatuses.COMPLETED, response.data['course_runs'][0]['course_run_status'])

        # course run has ended and user has earned a passing certificate
        mock_has_ended.return_value = True

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(CourseRunProgressStatuses.COMPLETED, response.data['course_runs'][0]['course_run_status'])

    @mock.patch.object(CourseOverview, 'has_ended')
    @mock.patch.object(CourseOverview, 'has_started')
    def test_course_run_status_self_paced_in_progress(self, mock_has_started, mock_has_ended):
        self.client.login(username=self.student.username, password=self.password)

        # set as self paced
        self.course_overview.self_paced = True
        self.course_overview.save()

        # course run has started and has not ended
        mock_has_started.return_value = True
        mock_has_ended.return_value = False

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(CourseRunProgressStatuses.IN_PROGRESS, response.data['course_runs'][0]['course_run_status'])

        # course run has not ended and user has earned a passing certificate fewer than 30 days ago
        certificate = self.create_generated_certificate()
        certificate.created_date = datetime.utcnow() - timedelta(5)
        certificate.save()

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(CourseRunProgressStatuses.IN_PROGRESS, response.data['course_runs'][0]['course_run_status'])

    @mock.patch.object(CourseOverview, 'has_ended')
    @mock.patch.object(CourseOverview, 'has_started')
    def test_course_run_status_self_paced_upcoming(self, mock_has_started, mock_has_ended):
        self.client.login(username=self.student.username, password=self.password)

        # set as self paced
        self.course_overview.self_paced = True
        self.course_overview.save()

        # course run has not started and has not ended
        mock_has_started.return_value = False
        mock_has_ended.return_value = False

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(CourseRunProgressStatuses.UPCOMING, response.data['course_runs'][0]['course_run_status'])

    def test_course_run_url(self):
        self.client.login(username=self.student.username, password=self.password)

        course_run_url = 'http://testserver/courses/{}/course/'.format(text_type(self.course_id))

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(course_run_url, response.data['course_runs'][0]['course_run_url'])

    def test_course_run_dates(self):
        self.client.login(username=self.student.username, password=self.password)

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        course_run_overview = response.data['course_runs'][0]

        self.assertEqual(course_run_overview['start_date'], '2018-12-31T00:00:00Z')
        self.assertEqual(course_run_overview['end_date'], '2019-01-02T00:00:00Z')

        # course run end date may not exist
        self.course_overview.end = None
        self.course_overview.save()

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(response.data['course_runs'][0]['end_date'], None)

    def test_course_run_id_and_display_name(self):
        self.client.login(username=self.student.username, password=self.password)

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        course_run_overview = response.data['course_runs'][0]

        self.assertEqual(course_run_overview['course_run_id'], text_type(self.course_id))
        self.assertEqual(course_run_overview['display_name'], "{} Course".format(text_type(self.course_id)))

    def test_emails_enabled(self):
        self.client.login(username=self.student.username, password=self.password)

        # by default, BulkEmailFlag is not enabled, so 'emails_enabled' won't be in the response
        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertNotIn('emails_enabled', response.data['course_runs'][0])

        with mock.patch.object(BulkEmailFlag, 'feature_enabled', return_value=True):
            response = self.client.get(self.get_url(self.program_uuid))
            self.assertEqual(status.HTTP_200_OK, response.status_code)
            self.assertTrue(response.data['course_runs'][0]['emails_enabled'])

            Optout.objects.create(
                user=self.student,
                course_id=self.course_id
            )
            response = self.client.get(self.get_url(self.program_uuid))
            self.assertEqual(status.HTTP_200_OK, response.status_code)
            self.assertFalse(response.data['course_runs'][0]['emails_enabled'])

    def test_micromasters_title(self):
        self.client.login(username=self.student.username, password=self.password)

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertNotIn('micromasters_title', response.data['course_runs'][0])

        self.program['type'] = 'MicroMasters'
        # update the program in the catalog cache
        self.set_program_in_catalog_cache(self.program_uuid, self.program)

        response = self.client.get(self.get_url(self.program_uuid))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIn('micromasters_title', response.data['course_runs'][0])
