from django.conf import settings
from django.core.urlresolvers import clear_url_caches, resolve

from django.test import TestCase
from django.test.utils import override_settings

from mock import patch
from nose.plugins.attrib import attr

import sys

from util.testing import UrlResetMixin


@attr('shard_1')
class FaviconTestCase(UrlResetMixin, TestCase):
    """
    Tests of the courseware favicon.
    """

    def test_favicon_redirect(self):
        resp = self.client.get("/favicon.ico")
        self.assertEqual(resp.status_code, 301)
        self.assertRedirects(
            resp,
            "/static/images/favicon.ico",
            status_code=301, target_status_code=404  # @@@ how to avoid 404?
        )

    @override_settings(FAVICON_PATH="images/foo.ico")
    def test_favicon_redirect_with_favicon_path_setting(self):
        self.reset_urls()

        resp = self.client.get("/favicon.ico")
        self.assertEqual(resp.status_code, 301)
        self.assertRedirects(
            resp,
            "/static/images/foo.ico",
            status_code=301, target_status_code=404  # @@@ how to avoid 404?
        )

    @patch.dict("django.conf.settings.FEATURES", {"USE_CUSTOM_THEME": True})
    @override_settings(FAVICON_PATH="images/bar_fav.ico")
    @override_settings(THEME_NAME="bar")
    def test_favicon_redirect_with_theme(self):
        self.assertEqual(settings.FEATURES["USE_CUSTOM_THEME"], True)
        self.reset_urls()

        resp = self.client.get("/favicon.ico")
        self.assertEqual(resp.status_code, 301)
        self.assertRedirects(
            resp,
            "/static/images/bar_fav.ico",
            status_code=301, target_status_code=404  # @@@ how to avoid 404?
        )
