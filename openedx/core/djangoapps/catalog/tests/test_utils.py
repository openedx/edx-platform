"""Tests covering utilities for integrating with the catalog service."""
# pylint: disable=missing-docstring
import copy

import ddt
import mock
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from student.tests.factories import UserFactory

from openedx.core.djangoapps.catalog.cache import PROGRAM_CACHE_KEY_TPL, SITE_PROGRAM_UUIDS_CACHE_KEY_TPL
from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.catalog.tests.factories import CourseRunFactory, ProgramFactory, ProgramTypeFactory
from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin
from openedx.core.djangoapps.catalog.utils import (
    get_course_runs,
    get_program_types,
    get_programs,
    get_programs_with_type
)
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms

UTILS_MODULE = 'openedx.core.djangoapps.catalog.utils'
User = get_user_model()  # pylint: disable=invalid-name


@skip_unless_lms
@mock.patch(UTILS_MODULE + '.logger.info')
@mock.patch(UTILS_MODULE + '.logger.warning')
class TestGetPrograms(CacheIsolationTestCase):
    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestGetPrograms, self).setUp()
        self.site = SiteFactory()

    def test_get_many(self, mock_warning, mock_info):
        programs = ProgramFactory.create_batch(3)

        # Cache details for 2 of 3 programs.
        partial_programs = {
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']): program for program in programs[:2]
        }
        cache.set_many(partial_programs, None)

        # When called before UUIDs are cached, the function should return an
        # empty list and log a warning.
        self.assertEqual(get_programs(self.site), [])
        mock_warning.assert_called_once_with('Failed to get program UUIDs from the cache.')
        mock_warning.reset_mock()

        # Cache UUIDs for all 3 programs.
        cache.set(
            SITE_PROGRAM_UUIDS_CACHE_KEY_TPL.format(domain=self.site.domain),
            [program['uuid'] for program in programs],
            None
        )

        actual_programs = get_programs(self.site)

        # The 2 cached programs should be returned while info and warning
        # messages should be logged for the missing one.
        self.assertEqual(
            set(program['uuid'] for program in actual_programs),
            set(program['uuid'] for program in partial_programs.values())
        )
        mock_info.assert_called_with('Failed to get details for 1 programs. Retrying.')
        mock_warning.assert_called_with(
            'Failed to get details for program {uuid} from the cache.'.format(uuid=programs[2]['uuid'])
        )
        mock_warning.reset_mock()

        # We can't use a set comparison here because these values are dictionaries
        # and aren't hashable. We've already verified that all programs came out
        # of the cache above, so all we need to do here is verify the accuracy of
        # the data itself.
        for program in actual_programs:
            key = PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid'])
            self.assertEqual(program, partial_programs[key])

        # Cache details for all 3 programs.
        all_programs = {
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']): program for program in programs
        }
        cache.set_many(all_programs, None)

        actual_programs = get_programs(self.site)

        # All 3 programs should be returned.
        self.assertEqual(
            set(program['uuid'] for program in actual_programs),
            set(program['uuid'] for program in all_programs.values())
        )
        self.assertFalse(mock_warning.called)

        for program in actual_programs:
            key = PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid'])
            self.assertEqual(program, all_programs[key])

    @mock.patch(UTILS_MODULE + '.cache')
    def test_get_many_with_missing(self, mock_cache, mock_warning, mock_info):
        programs = ProgramFactory.create_batch(3)

        all_programs = {
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']): program for program in programs
        }

        partial_programs = {
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']): program for program in programs[:2]
        }

        def fake_get_many(keys):
            if len(keys) == 1:
                return {PROGRAM_CACHE_KEY_TPL.format(uuid=programs[-1]['uuid']): programs[-1]}
            else:
                return partial_programs

        mock_cache.get.return_value = [program['uuid'] for program in programs]
        mock_cache.get_many.side_effect = fake_get_many

        actual_programs = get_programs(self.site)

        # All 3 cached programs should be returned. An info message should be
        # logged about the one that was initially missing, but the code should
        # be able to stitch together all the details.
        self.assertEqual(
            set(program['uuid'] for program in actual_programs),
            set(program['uuid'] for program in all_programs.values())
        )
        self.assertFalse(mock_warning.called)
        mock_info.assert_called_with('Failed to get details for 1 programs. Retrying.')

        for program in actual_programs:
            key = PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid'])
            self.assertEqual(program, all_programs[key])

    def test_get_one(self, mock_warning, _mock_info):
        expected_program = ProgramFactory()
        expected_uuid = expected_program['uuid']

        self.assertEqual(get_programs(self.site, uuid=expected_uuid), None)
        mock_warning.assert_called_once_with(
            'Failed to get details for program {uuid} from the cache.'.format(uuid=expected_uuid)
        )
        mock_warning.reset_mock()

        cache.set(
            PROGRAM_CACHE_KEY_TPL.format(uuid=expected_uuid),
            expected_program,
            None
        )

        actual_program = get_programs(self.site, uuid=expected_uuid)
        self.assertEqual(actual_program, expected_program)
        self.assertFalse(mock_warning.called)


@skip_unless_lms
@ddt.ddt
class TestGetProgramsWithType(TestCase):
    def setUp(self):
        super(TestGetProgramsWithType, self).setUp()
        self.site = SiteFactory()

    @mock.patch(UTILS_MODULE + '.get_programs')
    @mock.patch(UTILS_MODULE + '.get_program_types')
    def test_get_programs_with_type(self, mock_get_program_types, mock_get_programs):
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

        actual = get_programs_with_type(self.site)
        self.assertEqual(actual, programs_with_program_type)

    @ddt.data(False, True)
    @mock.patch(UTILS_MODULE + '.get_programs')
    @mock.patch(UTILS_MODULE + '.get_program_types')
    def test_get_programs_with_type_include_hidden(self, include_hidden, mock_get_program_types, mock_get_programs):
        """Verify get_programs_with_type returns the expected list of programs with include_hidden parameter."""
        programs_with_program_type = []
        programs = [ProgramFactory(hidden=False), ProgramFactory(hidden=True)]
        program_types = []

        for program in programs:
            if program['hidden'] and not include_hidden:
                continue

            program_type = ProgramTypeFactory(name=program['type'])
            program_types.append(program_type)

            program_with_type = copy.deepcopy(program)
            program_with_type['type'] = program_type
            programs_with_program_type.append(program_with_type)

        mock_get_programs.return_value = programs
        mock_get_program_types.return_value = program_types

        actual = get_programs_with_type(self.site, include_hidden=include_hidden)
        self.assertEqual(actual, programs_with_program_type)


@mock.patch(UTILS_MODULE + '.get_edx_api_data')
class TestGetProgramTypes(CatalogIntegrationMixin, TestCase):
    """Tests covering retrieval of program types from the catalog service."""
    @override_settings(COURSE_CATALOG_API_URL='https://api.example.com/v1/')
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

        for arg in (self.catalog_integration, 'course_runs'):
            self.assertIn(arg, args)

        self.assertEqual(kwargs['api']._store['base_url'], self.catalog_integration.get_internal_api_url())  # pylint: disable=protected-access

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

    @mock.patch(UTILS_MODULE + '.logger.error')
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
