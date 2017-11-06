from openedx.core.djangoapps.schedules.template_context import absolute_url
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms


@skip_unless_lms
class TestTemplateContext(CacheIsolationTestCase):
    def setUp(self):
        self.site = SiteFactory.create()
        self.site.domain = 'example.com'

    def test_absolute_url(self):
        absolute = absolute_url(self.site, '/foo/bar')
        self.assertEqual(absolute, 'https://example.com/foo/bar')

    def test_absolute_url_domain_lstrip(self):
        self.site.domain = 'example.com/'
        absolute = absolute_url(self.site, 'foo/bar')
        self.assertEqual(absolute, 'https://example.com/foo/bar')

    def test_absolute_url_already_absolute(self):
        absolute = absolute_url(self.site, 'https://some-cdn.com/foo/bar')
        self.assertEqual(absolute, 'https://some-cdn.com/foo/bar')
