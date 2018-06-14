""" Tests for journals marketing views. """

import mock

from django.conf import settings
from django.core.urlresolvers import reverse

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from openedx.features.journals.tests.utils import get_mocked_journal_bundle, get_mocked_pricing_data


class JournalMarketingViewTest(CacheIsolationTestCase, SiteMixin):
    """ Tests for the student account views that update the user's account information. """

    def setUp(self):
        super(JournalMarketingViewTest, self).setUp()
        self.path = reverse(
            "openedx.journals.bundle_about",
            kwargs={'bundle_uuid': "4837728d-6dab-458b-9e3f-3e799cfdc31c"}
        )

    @mock.patch.dict(settings.FEATURES, {"ENABLE_JOURNAL_INTEGRATION": True})
    @mock.patch('openedx.features.journals.api.DiscoveryApiClient.get_journal_bundles')
    def test_with_empty_data(self, mock_bundles):
        mock_bundles.return_value = []
        response = self.client.get(path=self.path)
        self.assertEqual(response.status_code, 404)

    @mock.patch.dict(settings.FEATURES, {"ENABLE_JOURNAL_INTEGRATION": True})
    @mock.patch('openedx.features.journals.views.marketing.get_pricing_data')
    @mock.patch('openedx.features.journals.api.DiscoveryApiClient.get_journal_bundles')
    def test_with_valid_data(self, mock_bundles, mock_pricing_data):
        mock_pricing_data.return_value = get_mocked_pricing_data()
        mock_bundles.return_value = get_mocked_journal_bundle()
        response = self.client.get(path=self.path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Purchase the Bundle")


