"""
Tests for course utils.
"""
from django.core.cache import cache
import httpretty
import mock
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.catalog.tests import factories
from openedx.core.djangoapps.catalog.utils import CatalogCacheUtility
from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from student.tests.factories import UserFactory
from util.course import get_link_for_about_page_from_cache, get_link_for_about_page


@httpretty.activate
class CourseAboutLinkTestCase(CatalogIntegrationMixin, CacheIsolationTestCase):
    """
    Tests for Course About link.
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(CourseAboutLinkTestCase, self).setUp()
        self.user = UserFactory.create(password="password")

        self.course_key_string = "foo/bar/baz"
        self.course_key = CourseKey.from_string("foo/bar/baz")
        self.course_run = factories.CourseRun(key=self.course_key_string)
        self.lms_course_about_url = "http://localhost:8000/courses/foo/bar/baz/about"

        self.catalog_integration = self.create_catalog_integration(
            internal_api_url="http://catalog.example.com:443/api/v1",
            cache_ttl=1
        )
        self.course_cache_key = "{}{}".format(CatalogCacheUtility.CACHE_KEY_PREFIX, self.course_key_string)

    def test_about_page_lms(self):
        """
        Get URL for about page, no marketing site.
        """
        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': False}):
            self.assertEquals(
                get_link_for_about_page(self.course_key, self.user), self.lms_course_about_url
            )
            self.assertEquals(
                get_link_for_about_page_from_cache(self.course_key, self.course_run), self.lms_course_about_url
            )
        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True}):
            self.register_catalog_course_run_response(
                [self.course_key_string], [{"key": self.course_key_string, "marketing_url": None}]
            )
            self.assertEquals(get_link_for_about_page(self.course_key, self.user), self.lms_course_about_url)

    @mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True})
    def test_about_page_marketing_site(self):
        """
        Get URL for about page, marketing site enabled.
        """
        self.register_catalog_course_run_response([self.course_key_string], [self.course_run])
        self.assertEquals(get_link_for_about_page(self.course_key, self.user), self.course_run["marketing_url"])
        cached_data = cache.get_many([self.course_cache_key])
        self.assertIn(self.course_cache_key, cached_data.keys())

        with mock.patch('openedx.core.djangoapps.catalog.utils.get_edx_api_data') as mock_method:
            self.assertEquals(get_link_for_about_page(self.course_key, self.user), self.course_run["marketing_url"])
            self.assertEqual(0, mock_method.call_count)

    @mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': True})
    def test_about_page_marketing_url_cached(self):
        self.assertEquals(
            get_link_for_about_page_from_cache(self.course_key, self.course_run),
            self.course_run["marketing_url"]
        )
