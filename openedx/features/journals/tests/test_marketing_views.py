""" Tests for journals marketing views. """

import uuid
import mock

from django.conf import settings
from django.core.urlresolvers import reverse

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from openedx.features.journals.tests.utils import get_mocked_journal_bundle, get_mocked_pricing_data


@mock.patch.dict(settings.FEATURES, {"ENABLE_JOURNAL_INTEGRATION": True})
class JournalMarketingViewTest(CacheIsolationTestCase, SiteMixin):
    """ Tests for journals marketing views. """

    @mock.patch('openedx.features.journals.api.DiscoveryApiClient.get_journal_bundles')
    def test_journal_bundle_with_empty_data(self, mock_bundles):
        """
        Test the marketing page without journal bundle data.
        """
        mock_bundles.return_value = []
        response = self.client.get(
            path=reverse(
                "openedx.journals.bundle_about",
                kwargs={'bundle_uuid': str(uuid.uuid4())}
            )
        )
        self.assertEqual(response.status_code, 404)

    @mock.patch('openedx.features.journals.views.marketing.get_pricing_data')
    @mock.patch('openedx.features.journals.api.DiscoveryApiClient.get_journal_bundles')
    def test_journal_bundle_with_valid_data(self, mock_bundles, mock_pricing_data):
        """
        Test the marketing page with journal bundle data.
        """
        journal_bundle = get_mocked_journal_bundle()
        mock_pricing_data.return_value = get_mocked_pricing_data()
        mock_bundles.return_value = journal_bundle
        response = self.client.get(
            path=reverse(
                "openedx.journals.bundle_about",
                kwargs={'bundle_uuid': str(uuid.uuid4())}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Purchase the Bundle")
        self.assertContains(response, journal_bundle["title"])
        self.assertContains(response, journal_bundle["courses"][0]["short_description"])
        self.assertContains(response, journal_bundle["courses"][0]["course_runs"][0]["title"])
