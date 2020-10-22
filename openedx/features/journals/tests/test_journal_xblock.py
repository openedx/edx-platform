"""
Test cases for journal page views.
"""

import uuid
import mock

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from lms.djangoapps.courseware.tests.helpers import LoginEnrollmentTestCase
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from openedx.features.journals.tests.utils import (
    get_mocked_journal_access,
    override_switch
)
from openedx.features.journals.api import JOURNAL_INTEGRATION


@mock.patch.dict(settings.FEATURES, {"JOURNALS_ENABLED": True})
class RenderXblockByJournalAccessViewTest(LoginEnrollmentTestCase, CacheIsolationTestCase, SiteMixin):
    """ Tests for views responsible for rendering xblock in journals """

    def setUp(self):
        super(RenderXblockByJournalAccessViewTest, self).setUp()
        self.setup_user()
        self.path = reverse(
            "openedx.journals.render_xblock_by_journal_access",
            kwargs={
                "usage_key_string": "block-v1:edX+DemoX+Demo_Course+type@video+block@5c90cffecd9b48b188cbfea176bf7fe9"
            }
        )

    @override_switch(JOURNAL_INTEGRATION, True)
    @mock.patch('openedx.features.journals.views.journal_xblock.fetch_journal_access')
    @mock.patch('openedx.features.journals.views.journal_xblock.render_xblock')
    def test_without_journal_access(self, mocked_render_xblock, mocked_journal_access):
        """
        Test the journal page without journal access.
        """
        mocked_journal_access.return_value = []
        mocked_render_xblock.return_value = []
        path = "{path}?journal_uuid={journal_uuid}".format(
            path=self.path,
            journal_uuid=str(uuid.uuid4())
        )
        response = self.client.get(path=path)
        self.assertEqual(response.status_code, 403)

    @override_switch(JOURNAL_INTEGRATION, True)
    @mock.patch('openedx.features.journals.views.journal_xblock.fetch_journal_access')
    @mock.patch('openedx.features.journals.views.journal_xblock.render_xblock')
    def test_unauthenticated_journal_access(self, mocked_render_xblock, mocked_journal_access):
        """
        Test when not logged in
        """
        self.logout()
        mocked_journal_access.return_value = []
        mocked_render_xblock.return_value = []
        path = "{path}?journal_uuid={journal_uuid}".format(
            path=self.path,
            journal_uuid=str(uuid.uuid4())
        )
        response = self.client.get(path=path)
        self.assertEqual(response.status_code, 403)

    @override_switch(JOURNAL_INTEGRATION, True)
    @mock.patch('openedx.features.journals.views.journal_xblock.fetch_journal_access')
    @mock.patch('openedx.features.journals.views.journal_xblock.render_xblock')
    def test_with_journal_access(self, mocked_render_xblock, mocked_journal_access):
        """
        Test the journal page with journal access.
        """
        journal_uuid = str(uuid.uuid4())
        mocked_journal_access.return_value = get_mocked_journal_access(journal_uuid=journal_uuid)
        mocked_render_xblock.return_value = HttpResponse("")
        path = "{path}?journal_uuid={journal_uuid}".format(
            path=self.path,
            journal_uuid=journal_uuid
        )
        response = self.client.get(path=path)
        self.assertEqual(response.status_code, 200)
        mocked_render_xblock.assert_called_once()
