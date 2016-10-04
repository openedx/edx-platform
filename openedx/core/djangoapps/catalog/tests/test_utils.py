"""Tests covering utilities for integrating with the catalog service."""
import uuid

import ddt
from django.test import TestCase
import mock
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.catalog import utils
from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.catalog.tests import factories, mixins
from student.tests.factories import UserFactory


UTILS_MODULE = 'openedx.core.djangoapps.catalog.utils'


@mock.patch(UTILS_MODULE + '.get_edx_api_data')
# ConfigurationModels use the cache. Make every cache get a miss.
@mock.patch('config_models.models.cache.get', return_value=None)
class TestGetPrograms(mixins.CatalogIntegrationMixin, TestCase):
    """Tests covering retrieval of programs from the catalog service."""
    def setUp(self):
        super(TestGetPrograms, self).setUp()

        self.user = UserFactory()
        self.uuid = str(uuid.uuid4())
        self.type = 'FooBar'
        self.catalog_integration = self.create_catalog_integration(cache_ttl=1)

    def assert_contract(self, call_args, program_uuid=None, type=None):  # pylint: disable=redefined-builtin
        """Verify that API data retrieval utility is used correctly."""
        args, kwargs = call_args

        for arg in (self.catalog_integration, self.user, 'programs'):
            self.assertIn(arg, args)

        self.assertEqual(kwargs['resource_id'], program_uuid)

        cache_key = '{base}.programs{type}'.format(
            base=self.catalog_integration.CACHE_KEY,
            type='.' + type if type else ''
        )
        self.assertEqual(
            kwargs['cache_key'],
            cache_key if self.catalog_integration.is_cache_enabled else None
        )

        self.assertEqual(kwargs['api']._store['base_url'], self.catalog_integration.internal_api_url)  # pylint: disable=protected-access

        querystring = {
            'marketable': 1,
            'exclude_utm': 1,
        }
        if type:
            querystring['type'] = type
        self.assertEqual(kwargs['querystring'], querystring)

        return args, kwargs

    def test_get_programs(self, _mock_cache, mock_get_catalog_data):
        programs = [factories.Program() for __ in range(3)]
        mock_get_catalog_data.return_value = programs

        data = utils.get_programs(self.user)

        self.assert_contract(mock_get_catalog_data.call_args)
        self.assertEqual(data, programs)

    def test_get_one_program(self, _mock_cache, mock_get_catalog_data):
        program = factories.Program()
        mock_get_catalog_data.return_value = program

        data = utils.get_programs(self.user, uuid=self.uuid)

        self.assert_contract(mock_get_catalog_data.call_args, program_uuid=self.uuid)
        self.assertEqual(data, program)

    def test_get_programs_by_type(self, _mock_cache, mock_get_catalog_data):
        programs = [factories.Program() for __ in range(2)]
        mock_get_catalog_data.return_value = programs

        data = utils.get_programs(self.user, type=self.type)

        self.assert_contract(mock_get_catalog_data.call_args, type=self.type)
        self.assertEqual(data, programs)

    def test_programs_unavailable(self, _mock_cache, mock_get_catalog_data):
        mock_get_catalog_data.return_value = []

        data = utils.get_programs(self.user)

        self.assert_contract(mock_get_catalog_data.call_args)
        self.assertEqual(data, [])

    def test_cache_disabled(self, _mock_cache, mock_get_catalog_data):
        self.catalog_integration = self.create_catalog_integration(cache_ttl=0)
        utils.get_programs(self.user)
        self.assert_contract(mock_get_catalog_data.call_args)

    def test_config_missing(self, _mock_cache, _mock_get_catalog_data):
        """Verify that no errors occur if this method is called when catalog config is missing."""
        CatalogIntegration.objects.all().delete()

        data = utils.get_programs(self.user)
        self.assertEqual(data, [])


class TestMungeCatalogProgram(TestCase):
    """Tests covering querystring stripping."""
    catalog_program = factories.Program()

    def test_munge_catalog_program(self):
        munged = utils.munge_catalog_program(self.catalog_program)
        expected = {
            'id': self.catalog_program['uuid'],
            'name': self.catalog_program['title'],
            'subtitle': self.catalog_program['subtitle'],
            'category': self.catalog_program['type'],
            'marketing_slug': self.catalog_program['marketing_slug'],
            'organizations': [
                {
                    'display_name': organization['name'],
                    'key': organization['key']
                } for organization in self.catalog_program['authoring_organizations']
            ],
            'course_codes': [
                {
                    'display_name': course['title'],
                    'key': course['key'],
                    'organization': {
                        'display_name': course['owners'][0]['name'],
                        'key': course['owners'][0]['key']
                    },
                    'run_modes': [
                        {
                            'course_key': run['key'],
                            'run_key': CourseKey.from_string(run['key']).run,
                            'mode_slug': 'verified'
                        } for run in course['course_runs']
                    ],
                } for course in self.catalog_program['courses']
            ],
            'banner_image_urls': {
                'w1440h480': self.catalog_program['banner_image']['large']['url'],
                'w726h242': self.catalog_program['banner_image']['medium']['url'],
                'w435h145': self.catalog_program['banner_image']['small']['url'],
                'w348h116': self.catalog_program['banner_image']['x-small']['url'],
            },
        }

        self.assertEqual(munged, expected)


@mock.patch(UTILS_MODULE + '.get_edx_api_data')
@mock.patch('config_models.models.cache.get', return_value=None)
class TestGetCourseRun(mixins.CatalogIntegrationMixin, TestCase):
    """Tests covering retrieval of course runs from the catalog service."""
    def setUp(self):
        super(TestGetCourseRun, self).setUp()

        self.user = UserFactory()
        self.course_key = CourseKey.from_string('foo/bar/baz')
        self.catalog_integration = self.create_catalog_integration()

    def assert_contract(self, call_args):
        """Verify that API data retrieval utility is used correctly."""
        args, kwargs = call_args

        for arg in (self.catalog_integration, self.user, 'course_runs'):
            self.assertIn(arg, args)

        self.assertEqual(kwargs['resource_id'], unicode(self.course_key))
        self.assertEqual(kwargs['api']._store['base_url'], self.catalog_integration.internal_api_url)  # pylint: disable=protected-access

        return args, kwargs

    def test_get_course_run(self, _mock_cache, mock_get_catalog_data):
        course_run = factories.CourseRun()
        mock_get_catalog_data.return_value = course_run

        data = utils.get_course_run(self.course_key, self.user)

        self.assert_contract(mock_get_catalog_data.call_args)
        self.assertEqual(data, course_run)

    def test_course_run_unavailable(self, _mock_cache, mock_get_catalog_data):
        mock_get_catalog_data.return_value = []

        data = utils.get_course_run(self.course_key, self.user)

        self.assert_contract(mock_get_catalog_data.call_args)
        self.assertEqual(data, {})

    def test_cache_disabled(self, _mock_cache, mock_get_catalog_data):
        utils.get_course_run(self.course_key, self.user)

        _, kwargs = self.assert_contract(mock_get_catalog_data.call_args)

        self.assertIsNone(kwargs['cache_key'])

    def test_cache_enabled(self, _mock_cache, mock_get_catalog_data):
        catalog_integration = self.create_catalog_integration(cache_ttl=1)

        utils.get_course_run(self.course_key, self.user)

        _, kwargs = mock_get_catalog_data.call_args

        self.assertEqual(kwargs['cache_key'], catalog_integration.CACHE_KEY)

    def test_config_missing(self, _mock_cache, _mock_get_catalog_data):
        """Verify that no errors occur if this method is called when catalog config is missing."""
        CatalogIntegration.objects.all().delete()

        data = utils.get_course_run(self.course_key, self.user)
        self.assertEqual(data, {})


@mock.patch(UTILS_MODULE + '.get_course_run')
class TestGetRunMarketingUrl(TestCase):
    """Tests covering retrieval of course run marketing URLs."""
    def setUp(self):
        super(TestGetRunMarketingUrl, self).setUp()

        self.course_key = CourseKey.from_string('foo/bar/baz')
        self.user = UserFactory()

    def test_get_run_marketing_url(self, mock_get_course_run):
        course_run = factories.CourseRun()
        mock_get_course_run.return_value = course_run

        url = utils.get_run_marketing_url(self.course_key, self.user)

        self.assertEqual(url, course_run['marketing_url'])

    def test_marketing_url_missing(self, mock_get_course_run):
        mock_get_course_run.return_value = {}

        url = utils.get_run_marketing_url(self.course_key, self.user)

        self.assertEqual(url, None)
