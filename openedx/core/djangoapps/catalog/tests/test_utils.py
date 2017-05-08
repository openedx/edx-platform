"""Tests covering utilities for integrating with the catalog service."""
# pylint: disable=missing-docstring
import copy
import uuid

import mock
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from openedx.core.djangoapps.catalog.cache import PROGRAM_CACHE_KEY_TPL, PROGRAM_UUIDS_CACHE_KEY
from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.catalog.tests.factories import CourseRunFactory, ProgramFactory, ProgramTypeFactory
from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin
from openedx.core.djangoapps.catalog.utils import (
    get_programs,
    get_program_types,
    get_programs_with_type,
    get_course_runs,
)
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from student.tests.factories import UserFactory


UTILS_MODULE = 'openedx.core.djangoapps.catalog.utils'
User = get_user_model()  # pylint: disable=invalid-name


@skip_unless_lms
@mock.patch(UTILS_MODULE + '.logger.warning')
class TestGetPrograms(CacheIsolationTestCase):
    ENABLED_CACHES = ['default']

    def test_get_many(self, mock_warning):
        programs = ProgramFactory.create_batch(3)

        # Cache details for 2 of 3 programs.
        partial_programs = {
            PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid']): program for program in programs[:2]
        }
        cache.set_many(partial_programs, None)

        # When called before UUIDs are cached, the function should return an empty
        # list and log a warning.
        self.assertEqual(get_programs(), [])
        mock_warning.assert_called_once_with('Program UUIDs are not cached.')
        mock_warning.reset_mock()

        # Cache UUIDs for all 3 programs.
        cache.set(
            PROGRAM_UUIDS_CACHE_KEY,
            [program['uuid'] for program in programs],
            None
        )

        actual_programs = get_programs()

        # The 2 cached programs should be returned while a warning should be logged
        # for the missing one.
        self.assertEqual(
            set(program['uuid'] for program in actual_programs),
            set(program['uuid'] for program in partial_programs.values())
        )
        mock_warning.assert_called_with(
            'Details for program {uuid} are not cached.'.format(uuid=programs[2]['uuid'])
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

        actual_programs = get_programs()

        # All 3 programs should be returned.
        self.assertEqual(
            set(program['uuid'] for program in actual_programs),
            set(program['uuid'] for program in all_programs.values())
        )
        self.assertFalse(mock_warning.called)

        for program in actual_programs:
            key = PROGRAM_CACHE_KEY_TPL.format(uuid=program['uuid'])
            self.assertEqual(program, all_programs[key])

    def test_get_one(self, mock_warning):
        expected_program = ProgramFactory()
        expected_uuid = expected_program['uuid']

        self.assertEqual(get_programs(uuid=expected_uuid), None)
        mock_warning.assert_called_once_with(
            'Details for program {uuid} are not cached.'.format(uuid=expected_uuid)
        )
        mock_warning.reset_mock()

        cache.set(
            PROGRAM_CACHE_KEY_TPL.format(uuid=expected_uuid),
            expected_program,
            None
        )

        actual_program = get_programs(uuid=expected_uuid)
        self.assertEqual(actual_program, expected_program)
        self.assertFalse(mock_warning.called)


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

        for arg in (self.catalog_integration, 'course_runs'):
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
