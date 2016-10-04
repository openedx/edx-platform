"""
Mixins for TestCase classes that need to account for multiple sites
"""
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory


class SiteMixin(object):
    """
    Mixin for setting up Site framework models
    """
    def setUp(self):
        super(SiteMixin, self).setUp()

        self.site = SiteFactory.create()
        self.site_configuration = SiteConfigurationFactory.create(
            site=self.site,
            values={
                "SITE_NAME": self.site.domain,
                "course_org_filter": "fakeX",
            }
        )

        self.site_other = SiteFactory.create(
            domain='testserver.fakeother',
            name='testserver.fakeother'
        )
        self.site_configuration_other = SiteConfigurationFactory.create(
            site=self.site_other,
            values={
                "SITE_NAME": self.site_other.domain,
                "course_org_filter": "fakeOtherX",
                "ENABLE_MKTG_SITE": True,
                "SHOW_ECOMMERCE_REPORTS": True,
                "MKTG_URLS": {
                    "ROOT": "https://marketing.fakeother",
                    "ABOUT": "/fake-about"
                }
            }
        )

        # Initialize client with default site domain
        self.use_site(self.site)

    def use_site(self, site):
        """
        # Initializes the test client with the domain of the given site
        """
        self.client = self.client_class(SERVER_NAME=site.domain)
