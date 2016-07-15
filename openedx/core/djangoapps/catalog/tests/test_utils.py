"""Tests covering utilities for integrating with the catalog service."""
import ddt
from django.test import TestCase
import mock
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.catalog import utils
from openedx.core.djangoapps.catalog.tests import factories, mixins
from student.tests.factories import UserFactory


UTILS_MODULE = 'openedx.core.djangoapps.catalog.utils'


@mock.patch(UTILS_MODULE + '.get_edx_api_data')
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

    def test_get_course_run(self, mock_get_catalog_data):
        course_run = factories.CourseRun()
        mock_get_catalog_data.return_value = course_run

        data = utils.get_course_run(self.course_key, self.user)

        self.assert_contract(mock_get_catalog_data.call_args)
        self.assertEqual(data, course_run)

    def test_course_run_unavailable(self, mock_get_catalog_data):
        mock_get_catalog_data.return_value = []

        data = utils.get_course_run(self.course_key, self.user)

        self.assert_contract(mock_get_catalog_data.call_args)
        self.assertEqual(data, {})

    def test_cache_disabled(self, mock_get_catalog_data):
        utils.get_course_run(self.course_key, self.user)

        _, kwargs = self.assert_contract(mock_get_catalog_data.call_args)

        self.assertIsNone(kwargs['cache_key'])

    def test_cache_enabled(self, mock_get_catalog_data):
        catalog_integration = self.create_catalog_integration(cache_ttl=1)

        utils.get_course_run(self.course_key, self.user)

        _, kwargs = mock_get_catalog_data.call_args

        self.assertEqual(kwargs['cache_key'], catalog_integration.CACHE_KEY)


@mock.patch(UTILS_MODULE + '.get_course_run')
@mock.patch(UTILS_MODULE + '.strip_querystring')
class TestGetRunMarketingUrl(TestCase):
    """Tests covering retrieval of course run marketing URLs."""
    def setUp(self):
        super(TestGetRunMarketingUrl, self).setUp()

        self.course_key = CourseKey.from_string('foo/bar/baz')
        self.user = UserFactory()

    def test_get_run_marketing_url(self, mock_strip, mock_get_course_run):
        course_run = factories.CourseRun()
        mock_get_course_run.return_value = course_run
        mock_strip.return_value = course_run['marketing_url']

        url = utils.get_run_marketing_url(self.course_key, self.user)

        self.assertTrue(mock_strip.called)
        self.assertEqual(url, course_run['marketing_url'])

    def test_marketing_url_empty(self, mock_strip, mock_get_course_run):
        course_run = factories.CourseRun()
        course_run['marketing_url'] = ''
        mock_get_course_run.return_value = course_run

        url = utils.get_run_marketing_url(self.course_key, self.user)

        self.assertFalse(mock_strip.called)
        self.assertEqual(url, None)

    def test_marketing_url_missing(self, mock_strip, mock_get_course_run):
        mock_get_course_run.return_value = {}

        url = utils.get_run_marketing_url(self.course_key, self.user)

        self.assertFalse(mock_strip.called)
        self.assertEqual(url, None)


@ddt.ddt
class TestStripQuerystring(TestCase):
    """Tests covering querystring stripping."""
    bare_url = 'https://www.example.com/path'

    @ddt.data(
        bare_url,
        bare_url + '?foo=bar&baz=qux',
    )
    def test_strip_querystring(self, url):
        self.assertEqual(utils.strip_querystring(url), self.bare_url)
