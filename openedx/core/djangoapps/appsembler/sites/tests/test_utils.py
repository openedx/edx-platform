import unittest
from mock import patch

from django.core.exceptions import ImproperlyConfigured, MultipleObjectsReturned
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from openedx.core.djangoapps.appsembler.api.tests.factories import OrganizationFactory
from openedx.core.djangoapps.appsembler.sites.utils import get_current_organization, get_initial_page_elements
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from organizations.models import Organization


class JSONMigrationUtilsTestCase(TestCase):
    def test_initial_page_elements(self):
        initial = get_initial_page_elements()

        self.assertEqual(initial['embargo'], {"content": []})

        element = initial['index']['content'][0]['children']['column-1'][0]

        self.assertEqual(element['options']['text-content'], {
            'en': 'Welcome to your Tahoe trial LMS site!',
        })


class OrganizationByRequestTestCase(TestCase):
    def setUp(self):
        super(OrganizationByRequestTestCase, self).setUp()
        self.siteFoo = SiteFactory.create(domain='foo.dev', name='foo.dev')
        self.siteBar = SiteFactory.create(domain='bar.dev', name='bar.dev')
        self.siteBaz = SiteFactory.create(domain='baz.dev', name='baz.dev')
        self.organizationA = OrganizationFactory(sites=[self.siteFoo])
        self.organizationB = OrganizationFactory(sites=[self.siteFoo])
        self.organizationC = OrganizationFactory(sites=[self.siteBar])
        self.request = RequestFactory().post('dummy_url')
        self.request.session = {}
        for patch_req in (
            'openedx.core.djangoapps.appsembler.sites.utils.get_current_request',
            'openedx.core.djangoapps.theming.helpers.get_current_request'
        ):
            patcher = patch(patch_req)
            patched_req = patcher.start()
            patched_req.return_value = self.request
            self.addCleanup(patcher.stop)

    @unittest.skip
    def test_amc_admin_user_no_org_in_request(self):
        # TODO: would be good to test
        pass

    @patch.dict('django.conf.settings.FEATURES', {'TAHOE_ENABLE_MULTI_ORGS_PER_SITE': False})
    def test_single_organization_multiorg_feature_off(self):
        self.request.site = self.siteBar
        current_org = get_current_organization()
        self.assertEqual(current_org, self.organizationC)

    @patch.dict('django.conf.settings.FEATURES', {'TAHOE_ENABLE_MULTI_ORGS_PER_SITE': False})
    def test_multiple_organization_multiorg_feature_off(self):
        self.request.site = self.siteFoo
        # fail raising exception if more than one org found for site when feature not enabled
        with self.assertRaises(MultipleObjectsReturned):
            get_current_organization()

    @patch.dict('django.conf.settings.FEATURES', {'TAHOE_ENABLE_MULTI_ORGS_PER_SITE': True})
    def test_multiple_organizations_multiorg_feature_on(self):
        self.request.site = self.siteFoo
        # return one org from Site's org relations
        current_org = get_current_organization()
        self.assertIn(current_org, (self.organizationA, self.organizationB))

    def test_no_org_for_site(self):
        self.request.site = self.siteBaz
        with self.assertRaises(Organization.DoesNotExist):
            get_current_organization()

    @patch.dict('django.conf.settings.FEATURES', {
        'TAHOE_ENABLE_MULTI_ORGS_PER_SITE': True,
        'APPSEMBLER_MULTI_TENANT_EMAILS': True
    })
    def test_raises_if_multiorg_feature_and_multitenant_email_feature_on(self):
        self.request.site = self.siteFoo
        with self.assertRaises(ImproperlyConfigured):
            get_current_organization()
