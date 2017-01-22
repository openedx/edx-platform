"""
Tests covering utilities for integrating with the catalog service.
"""
import uuid
import copy

from django.core.cache import cache
from django.test import TestCase
import httpretty
import mock
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.catalog import utils
from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.catalog.tests import factories, mixins
from student.tests.factories import UserFactory, AnonymousUserFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase


UTILS_MODULE = 'openedx.core.djangoapps.catalog.utils'


@mock.patch(UTILS_MODULE + '.get_edx_api_data')
# ConfigurationModels use the cache. Make every cache get a miss.
@mock.patch('config_models.models.cache.get', return_value=None)
class TestGetPrograms(mixins.CatalogIntegrationMixin, TestCase):
    """
    Tests covering retrieval of programs from the catalog service.
    """
    def setUp(self):
        super(TestGetPrograms, self).setUp()

        self.user = UserFactory()
        self.uuid = str(uuid.uuid4())
        self.type = 'FooBar'
        self.catalog_integration = self.create_catalog_integration(cache_ttl=1)

    def assert_contract(self, call_args, program_uuid=None, type=None):  # pylint: disable=redefined-builtin
        """
        Verify that API data retrieval utility is used correctly.
        """
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
            'published_course_runs_only': 1,
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

    def test_get_programs_anonymous_user(self, _mock_cache, mock_get_catalog_data):
        programs = [factories.Program() for __ in range(3)]
        mock_get_catalog_data.return_value = programs

        anonymous_user = AnonymousUserFactory()

        # The user is an Anonymous user but the Catalog Service User has not been created yet.
        data = utils.get_programs(anonymous_user)
        # This should not return programs.
        self.assertEqual(data, [])

        UserFactory(username='lms_catalog_service_user')
        # After creating the service user above,
        data = utils.get_programs(anonymous_user)
        # the programs should be returned successfully.
        self.assertEqual(data, programs)

    def test_get_program_types(self, _mock_cache, mock_get_catalog_data):
        program_types = [factories.ProgramType() for __ in range(3)]
        mock_get_catalog_data.return_value = program_types

        # Creating Anonymous user but the Catalog Service User has not been created yet.
        anonymous_user = AnonymousUserFactory()
        data = utils.get_program_types(anonymous_user)
        # This should not return programs.
        self.assertEqual(data, [])

        # Creating Catalog Service User user
        UserFactory(username='lms_catalog_service_user')
        data = utils.get_program_types(anonymous_user)
        # the programs should be returned successfully.
        self.assertEqual(data, program_types)

        # Catalog integration is disabled now.
        self.catalog_integration = self.create_catalog_integration(enabled=False)
        data = utils.get_program_types(anonymous_user)
        # This should not return programs.
        self.assertEqual(data, [])

    def test_get_programs_data(self, _mock_cache, mock_get_catalog_data):   # pylint: disable=unused-argument
        programs = []
        program_types = []
        programs_data = []

        for index in range(3):
            # Creating the Programs and their corresponding program types.
            type_name = "type_name_{postfix}".format(postfix=index)
            program = factories.Program(type=type_name)
            program_type = factories.ProgramType(name=type_name)

            # Maintaining the programs, program types and program data(program+logo_image) lists.
            programs.append(program)
            program_types.append(program_type)
            programs_data.append(copy.deepcopy(program))

            # Adding the logo image in program data.
            programs_data[-1]['logo_image'] = program_type["logo_image"]

        with mock.patch("openedx.core.djangoapps.catalog.utils.get_programs") as patched_get_programs:
            with mock.patch("openedx.core.djangoapps.catalog.utils.get_program_types") as patched_get_program_types:
                # Mocked the "get_programs" and "get_program_types"
                patched_get_programs.return_value = programs
                patched_get_program_types.return_value = program_types

                programs_data = utils.get_programs_data()
                self.assertEqual(programs_data, programs)

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
    """
    Tests covering querystring stripping.
    """
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


@httpretty.activate
class TestGetCourseRun(mixins.CatalogIntegrationMixin, CacheIsolationTestCase):
    """
    Tests covering retrieval of course runs from the catalog service.
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestGetCourseRun, self).setUp()

        self.user = UserFactory()
        self.catalog_integration = self.create_catalog_integration(
            internal_api_url="http://catalog.example.com:443/api/v1",
            cache_ttl=1,
        )
        self.course_runs = [factories.CourseRun() for __ in range(4)]
        self.course_key_1 = CourseKey.from_string(self.course_runs[0]["key"])
        self.course_key_2 = CourseKey.from_string(self.course_runs[1]["key"])
        self.course_key_3 = CourseKey.from_string(self.course_runs[2]["key"])
        self.course_key_4 = CourseKey.from_string(self.course_runs[3]["key"])

    def test_config_missing(self):
        """
        Verify that no errors occur if this method is called when catalog config is missing.
        """
        CatalogIntegration.objects.all().delete()

        data = utils.get_course_runs([], self.user)
        self.assertEqual(data, {})

    def test_get_course_run(self):
        course_keys = [self.course_key_1]
        course_key_strings = [self.course_runs[0]["key"]]
        self.register_catalog_course_run_response(course_key_strings, [self.course_runs[0]])

        course_catalog_data_dict = utils.get_course_runs(course_keys, self.user)
        expected_data = {self.course_runs[0]["key"]: self.course_runs[0]}
        self.assertEqual(expected_data, course_catalog_data_dict)

    def test_get_multiple_course_run(self):
        course_key_strings = [self.course_runs[0]["key"], self.course_runs[1]["key"], self.course_runs[2]["key"]]
        course_keys = [self.course_key_1, self.course_key_2, self.course_key_3]
        self.register_catalog_course_run_response(
            course_key_strings, [self.course_runs[0], self.course_runs[1], self.course_runs[2]]
        )

        course_catalog_data_dict = utils.get_course_runs(course_keys, self.user)
        expected_data = {
            self.course_runs[0]["key"]: self.course_runs[0],
            self.course_runs[1]["key"]: self.course_runs[1],
            self.course_runs[2]["key"]: self.course_runs[2],
        }
        self.assertEqual(expected_data, course_catalog_data_dict)

    def test_course_run_unavailable(self):
        course_key_strings = [self.course_runs[0]["key"], self.course_runs[3]["key"]]
        course_keys = [self.course_key_1, self.course_key_4]
        self.register_catalog_course_run_response(course_key_strings, [self.course_runs[0]])

        course_catalog_data_dict = utils.get_course_runs(course_keys, self.user)
        expected_data = {self.course_runs[0]["key"]: self.course_runs[0]}
        self.assertEqual(expected_data, course_catalog_data_dict)

    def test_cached_course_run_data(self):
        course_key_strings = [self.course_runs[0]["key"], self.course_runs[1]["key"]]
        course_keys = [self.course_key_1, self.course_key_2]
        course_cached_keys = [
            "{}{}".format(utils.CatalogCacheUtility.CACHE_KEY_PREFIX, self.course_runs[0]["key"]),
            "{}{}".format(utils.CatalogCacheUtility.CACHE_KEY_PREFIX, self.course_runs[1]["key"]),
        ]
        self.register_catalog_course_run_response(course_key_strings, [self.course_runs[0], self.course_runs[1]])
        expected_data = {
            self.course_runs[0]["key"]: self.course_runs[0],
            self.course_runs[1]["key"]: self.course_runs[1],
        }

        course_catalog_data_dict = utils.get_course_runs(course_keys, self.user)
        self.assertEqual(expected_data, course_catalog_data_dict)
        cached_data = cache.get_many(course_cached_keys)
        self.assertEqual(set(course_cached_keys), set(cached_data.keys()))

        with mock.patch('openedx.core.djangoapps.catalog.utils.get_edx_api_data') as mock_method:
            course_catalog_data_dict = utils.get_course_runs(course_keys, self.user)
            self.assertEqual(0, mock_method.call_count)
            self.assertEqual(expected_data, course_catalog_data_dict)


class TestGetRunMarketingUrl(TestCase, mixins.CatalogIntegrationMixin):
    """
    Tests covering retrieval of course run marketing URLs.
    """
    def setUp(self):
        super(TestGetRunMarketingUrl, self).setUp()
        self.user = UserFactory()
        self.course_runs = [factories.CourseRun() for __ in range(2)]
        self.course_key_1 = CourseKey.from_string(self.course_runs[0]["key"])

    def test_get_run_marketing_url(self):
        with mock.patch('openedx.core.djangoapps.catalog.utils.get_course_runs', return_value={
            self.course_runs[0]["key"]: self.course_runs[0],
            self.course_runs[1]["key"]: self.course_runs[1],
        }):
            course_marketing_url = utils.get_run_marketing_url(self.course_key_1, self.user)
            self.assertEqual(self.course_runs[0]["marketing_url"], course_marketing_url)

    def test_marketing_url_catalog_course_run_not_found(self):
        with mock.patch('openedx.core.djangoapps.catalog.utils.get_course_runs', return_value={
            self.course_runs[0]["key"]: self.course_runs[0],
        }):
            course_marketing_url = utils.get_run_marketing_url(self.course_key_1, self.user)
            self.assertEqual(self.course_runs[0]["marketing_url"], course_marketing_url)

    def test_marketing_url_missing(self):
        self.course_runs[1]["marketing_url"] = None
        with mock.patch('openedx.core.djangoapps.catalog.utils.get_course_runs', return_value={
            self.course_runs[0]["key"]: self.course_runs[0],
            self.course_runs[1]["key"]: self.course_runs[1],
        }):
            course_marketing_url = utils.get_run_marketing_url(CourseKey.from_string("foo2/bar2/baz2"), self.user)
            self.assertEqual(None, course_marketing_url)


class TestGetRunMarketingUrls(TestCase, mixins.CatalogIntegrationMixin):
    """
    Tests covering retrieval of course run marketing URLs.
    """
    def setUp(self):
        super(TestGetRunMarketingUrls, self).setUp()
        self.user = UserFactory()
        self.course_runs = [factories.CourseRun() for __ in range(2)]
        self.course_keys = [
            CourseKey.from_string(self.course_runs[0]["key"]),
            CourseKey.from_string(self.course_runs[1]["key"]),
        ]

    def test_get_run_marketing_url(self):
        expected_data = {
            self.course_runs[0]["key"]: self.course_runs[0]["marketing_url"],
            self.course_runs[1]["key"]: self.course_runs[1]["marketing_url"],
        }
        with mock.patch('openedx.core.djangoapps.catalog.utils.get_course_runs', return_value={
            self.course_runs[0]["key"]: self.course_runs[0],
            self.course_runs[1]["key"]: self.course_runs[1],
        }):
            course_marketing_url_dict = utils.get_run_marketing_urls(self.course_keys, self.user)
            self.assertEqual(expected_data, course_marketing_url_dict)

    def test_marketing_url_catalog_course_run_not_found(self):
        expected_data = {
            self.course_runs[0]["key"]: self.course_runs[0]["marketing_url"],
        }
        with mock.patch('openedx.core.djangoapps.catalog.utils.get_course_runs', return_value={
            self.course_runs[0]["key"]: self.course_runs[0],
        }):
            course_marketing_url_dict = utils.get_run_marketing_urls(self.course_keys, self.user)
            self.assertEqual(expected_data, course_marketing_url_dict)

    def test_marketing_url_missing(self):
        expected_data = {
            self.course_runs[0]["key"]: self.course_runs[0]["marketing_url"],
            self.course_runs[1]["key"]: None,
        }
        self.course_runs[1]["marketing_url"] = None
        with mock.patch('openedx.core.djangoapps.catalog.utils.get_course_runs', return_value={
            self.course_runs[0]["key"]: self.course_runs[0],
            self.course_runs[1]["key"]: self.course_runs[1],
        }):
            course_marketing_url_dict = utils.get_run_marketing_urls(self.course_keys, self.user)
            self.assertEqual(expected_data, course_marketing_url_dict)
