""" Tests for the v1 program enrollment API Views """
import json
from uuid import uuid4
import ddt
from django.contrib.auth.models import Permission
from django.core.cache import cache
from lms.djangoapps.program_enrollments.api.v1.constants import CourseEnrollmentResponseStatuses as CourseStatuses
from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment
from lms.djangoapps.program_enrollments.tests.factories import ProgramEnrollmentFactory, ProgramCourseEnrollmentFactory
from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.api.tests.mixins import JwtMixin
from openedx.core.djangoapps.catalog.tests.factories import (
    CourseFactory,
    OrganizationFactory as CatalogOrganizationFactory,
    ProgramFactory,
)
from openedx.core.djangolib.testing.utils import CacheIsolationMixin
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.catalog.cache import PROGRAM_CACHE_KEY_TPL
from rest_framework.test import APITestCase
from student.tests.factories import UserFactory, GroupFactory


class RequestMixin(JwtMixin):
    """
    Mixin with authenticated get/post/put/patch/delete helper functions.

    Expects implementing classes to provide ``self.client`` attribute.
    """

    def get(self, path, user):
        """
        Perform a GET on the given path, optionally with a user.
        """
        return self._request('get', path, user)

    def post(self, path, data, user):
        """
        Perform a POST on the given path, optionally with a user.
        """
        return self._request('post', path, user, data)

    def put(self, path, data, user):
        """
        Perform a PUT on the given path, optionally with a user.
        """
        return self._request('put', path, user, data)

    def patch(self, path, data, user):
        """
        Perform a PATCH on the given path, optionally with a user.
        """
        return self._request('patch', path, user, data)

    def delete(self, path, user):
        """
        Perform a DELETE on the given, optionally with a user.
        """
        return self._request('delete', path, user)

    def _request(self, method, path, user, data=None):
        """
        Perform an HTTP request of the given method.

        If user is not None, include a JWT auth header.
        """
        kwargs = {'follow': True}
        if user:
            kwargs['HTTP_AUTHORIZATION'] = self.generate_jwt_header(user)
        if data:
            kwargs['data'] = json.dumps(data)
            kwargs['content_type'] = 'application/json'
        return getattr(self.client, method.lower())(path, **kwargs)


class MockAPITestMixin(RequestMixin):
    """ Base mixin for tests for the v1 API. """
    api_root = '/api/program_enrollments/v1/'
    path_suffix = None  # Define me in subclasses

    @property
    def path(self):
        return self.api_root + self.path_suffix

    def setUp(self):
        super(MockAPITestMixin, self).setUp()
        self.user = UserFactory()
        permission_names = [
            'add_programenrollment',
            'change_programenrollment',
            'delete_programenrollment',
            'add_programcourseenrollment',
            'change_programcourseenrollment',
            'delete_programcourseenrollment',
        ]
        self.admin_program_enrollment_group = GroupFactory(
            name='admin_program_enrollment',
        )
        for permission_name in permission_names:
            self.admin_program_enrollment_group.permissions.add(
                Permission.objects.get(codename=permission_name)
            )
        self.admin_user = UserFactory(groups=[self.admin_program_enrollment_group])

    def test_unauthenticated(self):
        response = self.get(self.path, None)
        self.assertEqual(response.status_code, 401)


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
class CourseEnrollmentPostTests(MockAPITestMixin, APITestCase, ProgramCacheTestCaseMixin):
    """ Tests for mock course enrollment """

    @classmethod
    def setUpClass(cls):
        super(CourseEnrollmentPostTests, cls).setUpClass()
        cls.start_cache_isolation()

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
        self.path_suffix = self.build_path(self.program_uuid, self.course_run["key"])

    def learner_enrollment(self, student_key, status="active"):
        """
        Convenience method to create a learner enrollment record
        """
        return {"student_key": student_key, "status": status}

    def build_path(self, program_uuid, course):
        """
        Convenience method to build a path for a program course enrollment request
        """
        return 'programs/{}/course/{}/enrollments/'.format(program_uuid, course)

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
        response = self.post(self.path, post_data, self.admin_user)
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
            program_enrollment__external_user_key=external_user_key
        )
        self.assertEqual(expected_status, enrollment.status)
        course_enrollment = enrollment.course_enrollment
        if has_user:
            self.assertTrue(bool(course_enrollment))
            self.assertEqual(expected_status == "active", course_enrollment.is_active)
        else:
            self.assertEqual(None, course_enrollment)

    def test_duplicate(self):
        post_data = [
            self.learner_enrollment("l1", "active"),
            self.learner_enrollment("l1", "active"),
        ]
        response = self.post(self.path, post_data, self.admin_user)
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
        response = self.post(self.path, post_data, self.admin_user)
        self.assertEqual(422, response.status_code)
        self.assertDictEqual({'l1': CourseStatuses.CONFLICT}, response.data)

    def test_user_not_in_program(self):
        self.create_program_enrollment('l1')
        post_data = [
            self.learner_enrollment("l1"),
            self.learner_enrollment("l2"),
        ]
        response = self.post(self.path, post_data, self.admin_user)
        self.assertEqual(207, response.status_code)
        self.assertDictEqual(
            {
                "l1": "active",
                "l2": "not-in-program",
            },
            response.data
        )

    # def test_403_forbidden(self):
    #     post_data = [self.learner_enrollment("A")]
    #     response = self.post(self.path, post_data, self.user)
    #     self.assertEqual(403, response.status_code)

    def test_413_payload_too_large(self):
        post_data = [self.learner_enrollment(str(i)) for i in range(30)]
        response = self.post(self.path, post_data, self.admin_user)
        self.assertEqual(413, response.status_code)

    def test_404_not_found_program(self):
        paths = [
            self.build_path("nonexistant-program", self.course_run["key"]),
            self.build_path(self.program["uuid"], "nonexistant-course"),
            self.build_path(self.program["uuid"], self.course_not_in_program["key"]),
        ]
        post_data = [self.learner_enrollment("A")]
        for path_404 in paths:
            response = self.post(path_404, post_data, self.user)
            self.assertEqual(404, response.status_code)

    def test_invalid_status(self):
        post_data = [self.learner_enrollment('A', 'this-is-not-a-status')]
        response = self.post(self.path, post_data, self.admin_user)
        self.assertEqual(422, response.status_code)
        self.assertDictEqual({'A': CourseStatuses.INVALID_STATUS}, response.data)

    @ddt.data(
        [{'status': 'active'}],
        [{'student_key': '000'}],
        ["this isn't even a dict!"],
        [{'student_key': '000', 'status': 'active'}, "bad_data"],
    )
    def test_422_unprocessable_entity_bad_data(self, post_data):
        response = self.post(self.path, post_data, self.admin_user)
        self.assertEqual(response.status_code, 422)
        self.assertIn('invalid enrollment record', response.data)
