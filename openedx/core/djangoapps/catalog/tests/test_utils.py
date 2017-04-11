"""Tests covering utilities for integrating with the catalog service."""
# pylint: disable=missing-docstring
import copy
import uuid

import mock
from django.contrib.auth import get_user_model
from django.test import TestCase
from waffle.models import Switch

from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.catalog.tests.factories import CourseRunFactory, ProgramFactory, ProgramTypeFactory
from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin
from openedx.core.djangoapps.catalog.utils import (
    get_programs,
    get_program_types,
    get_programs_with_type,
    get_course_runs,
)
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import UserFactory

UTILS_MODULE = 'openedx.core.djangoapps.catalog.utils'
User = get_user_model()  # pylint: disable=invalid-name


@skip_unless_lms
@mock.patch(UTILS_MODULE + '.get_edx_api_data')
class TestGetPrograms(CatalogIntegrationMixin, TestCase):
    """Tests covering retrieval of programs from the catalog service."""
    def setUp(self):
        super(TestGetPrograms, self).setUp()

        self.uuid = str(uuid.uuid4())
        self.types = ['Foo', 'Bar', 'FooBar']
        self.catalog_integration = self.create_catalog_integration(cache_ttl=1)

        UserFactory(username=self.catalog_integration.service_username)

    def assert_contract(self, call_args, program_uuid=None, types=None):
        """Verify that API data retrieval utility is used correctly."""
        args, kwargs = call_args

        for arg in (self.catalog_integration, 'programs'):
            self.assertIn(arg, args)

        self.assertEqual(kwargs['resource_id'], program_uuid)

        types_param = ','.join(types) if types and isinstance(types, list) else None
        cache_key = '{base}.programs{types}'.format(
            base=self.catalog_integration.CACHE_KEY,
            types='.' + types_param if types_param else ''
        )
        self.assertEqual(
            kwargs['cache_key'],
            cache_key if self.catalog_integration.is_cache_enabled else None
        )

        self.assertEqual(kwargs['api']._store['base_url'], self.catalog_integration.internal_api_url)  # pylint: disable=protected-access

        querystring = {
            'exclude_utm': 1,
            'status': ('active', 'retired',),
        }
        if program_uuid:
            querystring['use_full_course_serializer'] = 1
        if types:
            querystring['types'] = types_param

        self.assertEqual(kwargs['querystring'], querystring)

        return args, kwargs

    def test_get_programs(self, mock_get_edx_api_data):
        programs = ProgramFactory.create_batch(3)
        mock_get_edx_api_data.return_value = programs

        data = get_programs()

        self.assert_contract(mock_get_edx_api_data.call_args)
        self.assertEqual(data, programs)

    def test_get_one_program(self, mock_get_edx_api_data):
        program = ProgramFactory()
        mock_get_edx_api_data.return_value = program

        data = get_programs(uuid=self.uuid)

        self.assert_contract(mock_get_edx_api_data.call_args, program_uuid=self.uuid)
        self.assertEqual(data, program)

    def test_get_programs_by_types(self, mock_get_edx_api_data):
        programs = ProgramFactory.create_batch(2)
        mock_get_edx_api_data.return_value = programs

        data = get_programs(types=self.types)

        self.assert_contract(mock_get_edx_api_data.call_args, types=self.types)
        self.assertEqual(data, programs)

    def test_programs_unavailable(self, mock_get_edx_api_data):
        mock_get_edx_api_data.return_value = []

        data = get_programs()

        self.assert_contract(mock_get_edx_api_data.call_args)
        self.assertEqual(data, [])

    def test_cache_disabled(self, mock_get_edx_api_data):
        self.catalog_integration = self.create_catalog_integration(cache_ttl=0)
        get_programs()
        self.assert_contract(mock_get_edx_api_data.call_args)

    def test_config_missing(self, _mock_get_edx_api_data):
        """
        Verify that no errors occur if this method is called when catalog config
        is missing.
        """
        CatalogIntegration.objects.all().delete()

        data = get_programs()
        self.assertEqual(data, [])

    def test_service_user_missing(self, _mock_get_edx_api_data):
        """
        Verify that no errors occur if this method is called when the catalog
        service user is missing.
        """
        # Note: Deleting the service user would be ideal, but causes mysterious
        # errors on Jenkins.
        self.create_catalog_integration(service_username='nonexistent-user')

        data = get_programs()
        self.assertEqual(data, [])

    @mock.patch(UTILS_MODULE + '.get_programs')
    @mock.patch(UTILS_MODULE + '.get_program_types')
    def test_get_programs_with_type(self, mock_get_program_types, mock_get_programs, _mock_get_edx_api_data):
        """Verify get_programs_with_type returns the expected list of programs."""
        programs_with_program_type = []
        programs = ProgramFactory.create_batch(2)
        program_types = []

        for program in programs:
            program_type = ProgramTypeFactory(name=program['type'])
            program_types.append(program_type)

            program_with_type = copy.deepcopy(program)
            program_with_type['type'] = program_type
            programs_with_program_type.append(program_with_type)

        mock_get_programs.return_value = programs
        mock_get_program_types.return_value = program_types

        actual = get_programs_with_type()

        self.assertEqual(actual, programs_with_program_type)


@skip_unless_lms
@mock.patch(UTILS_MODULE + '.get_edx_api_data')
class TestGetProgramTypes(CatalogIntegrationMixin, TestCase):
    """Tests covering retrieval of program types from the catalog service."""
    def test_get_program_types(self, mock_get_edx_api_data):
        """Verify get_program_types returns the expected list of program types."""
        program_types = ProgramTypeFactory.create_batch(3)
        mock_get_edx_api_data.return_value = program_types

        # Catalog integration is disabled.
        data = get_program_types()
        self.assertEqual(data, [])

        catalog_integration = self.create_catalog_integration()
        UserFactory(username=catalog_integration.service_username)
        data = get_program_types()
        self.assertEqual(data, program_types)

        program = program_types[0]
        data = get_program_types(name=program['name'])
        self.assertEqual(data, program)


@skip_unless_lms
@mock.patch(UTILS_MODULE + '.get_edx_api_data')
class TestGetCourseRuns(CatalogIntegrationMixin, TestCase):
    """
    Tests covering retrieval of course runs from the catalog service.
    """
    def setUp(self):
        super(TestGetCourseRuns, self).setUp()

        self.catalog_integration = self.create_catalog_integration(cache_ttl=1)
        self.user = UserFactory(username=self.catalog_integration.service_username)

    def assert_contract(self, call_args):  # pylint: disable=redefined-builtin
        """
        Verify that API data retrieval utility is used correctly.
        """
        args, kwargs = call_args

        for arg in (self.catalog_integration, self.user, 'course_runs'):
            self.assertIn(arg, args)

        self.assertEqual(kwargs['api']._store['base_url'], self.catalog_integration.internal_api_url)  # pylint: disable=protected-access

        querystring = {
            'page_size': 20,
            'exclude_utm': 1,
        }

        self.assertEqual(kwargs['querystring'], querystring)

        return args, kwargs

    def test_config_missing(self, mock_get_edx_api_data):
        """
        Verify that no errors occur when catalog config is missing.
        """
        CatalogIntegration.objects.all().delete()

        data = get_course_runs()
        self.assertFalse(mock_get_edx_api_data.called)
        self.assertEqual(data, [])

    @mock.patch(UTILS_MODULE + '.log.error')
    def test_service_user_missing(self, mock_log_error, mock_get_edx_api_data):
        """
        Verify that no errors occur when the catalog service user is missing.
        """
        catalog_integration = self.create_catalog_integration(service_username='nonexistent-user')

        data = get_course_runs()
        mock_log_error.any_call(
            'Catalog service user with username [%s] does not exist. Course runs will not be retrieved.',
            catalog_integration.service_username,
        )
        self.assertFalse(mock_get_edx_api_data.called)
        self.assertEqual(data, [])

    def test_get_course_runs(self, mock_get_edx_api_data):
        """
        Test retrieval of course runs.
        """
        catalog_course_runs = CourseRunFactory.create_batch(10)
        mock_get_edx_api_data.return_value = catalog_course_runs

        data = get_course_runs()
        self.assertTrue(mock_get_edx_api_data.called)
        self.assert_contract(mock_get_edx_api_data.call_args)
        self.assertEqual(data, catalog_course_runs)
