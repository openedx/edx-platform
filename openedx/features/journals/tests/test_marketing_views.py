""" Tests for journals marketing views. """

import uuid
import mock

from django.conf import settings
from django.core.urlresolvers import reverse

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from openedx.features.journals.tests.utils import (get_mocked_journals,
                                                   get_mocked_journal_bundles,
                                                   get_mocked_pricing_data,
                                                   override_switch)
from openedx.features.journals.api import JOURNAL_INTEGRATION
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@mock.patch.dict(settings.FEATURES, {"JOURNALS_ENABLED": True})
class JournalBundleViewTest(CacheIsolationTestCase, SiteMixin):
    """ Tests for journals marketing views. """

    @override_switch(JOURNAL_INTEGRATION, True)
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

    @override_switch(JOURNAL_INTEGRATION, True)
    @mock.patch('openedx.features.journals.views.marketing.get_pricing_data')
    @mock.patch('openedx.features.journals.api.DiscoveryApiClient.get_journal_bundles')
    def test_journal_bundle_with_valid_data(self, mock_bundles, mock_pricing_data):
        """
        Test the marketing page with journal bundle data.
        """
        journal_bundles = get_mocked_journal_bundles()
        journal_bundle = journal_bundles[0]
        mock_pricing_data.return_value = get_mocked_pricing_data()
        mock_bundles.return_value = journal_bundles
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


@mock.patch.dict(settings.FEATURES, {"JOURNALS_ENABLED": True})
class JournalIndexViewTest(SiteMixin, ModuleStoreTestCase):
    """
    Tests for Journals Listing in Marketing Pages.
    """
    shard = 1

    def setUp(self):
        super(JournalIndexViewTest, self).setUp()
        self.journal_bundles = get_mocked_journal_bundles()
        self.journal_bundle = self.journal_bundles[0]
        self.journals = get_mocked_journals()

    def assert_journal_data(self, response):
        """
        Checks the journal data in given response
        """
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bundle")
        self.assertContains(response, self.journal_bundle["uuid"])
        self.assertContains(response, self.journal_bundle["title"])
        self.assertContains(response, self.journal_bundle["organization"])
        for journal in self.journals:
            self.assertContains(response, "Journal")
            self.assertContains(response, journal["title"])
            self.assertContains(response, journal["organization"])

    @override_switch(JOURNAL_INTEGRATION, True)
    @mock.patch('student.views.management.get_journals_context')
    def test_journals_index_page(self, mock_journals_context):
        """
        Test the journal data on index page.
        """
        mock_journals_context.return_value = {'journal_bundles': self.journal_bundles, 'journals': self.journals}

        response = self.client.get(reverse('root'))
        self.assert_journal_data(response)

    @override_switch(JOURNAL_INTEGRATION, False)
    def test_journals_index_page_disabled(self):
        """
        Test the index page can load with journals disabled
        """
        response = self.client.get(reverse('root'))
        self.assertEqual(response.status_code, 200)

    @override_switch(JOURNAL_INTEGRATION, True)
    @mock.patch('openedx.features.journals.api.DiscoveryApiClient.get_journals')
    @mock.patch('openedx.features.journals.api.DiscoveryApiClient.get_journal_bundles')
    def test_journals_courses_page(self, mock_journal_bundles, mock_journals):
        """
        Test the journal data on courses page.
        """
        mock_journal_bundles.return_value = self.journal_bundles
        mock_journals.return_value = self.journals

        response = self.client.get(reverse('courses'))
        self.assert_journal_data(response)

    @override_switch(JOURNAL_INTEGRATION, False)
    def test_journals_courses_page_disabled(self):
        """
        Test the courses pages can load with journals disabled
        """
        response = self.client.get(reverse('courses'))
        self.assertEqual(response.status_code, 200)
