"""
Tests of the courseware favicon
"""


from django.test import TestCase
from django.test.utils import override_settings

from common.djangoapps.util.testing import UrlResetMixin


class FaviconTestCase(UrlResetMixin, TestCase):
    """
    Tests of the courseware favicon.
    """

    def test_favicon_redirect(self):
        resp = self.client.get("/favicon.ico")
        assert resp.status_code == 301
        self.assertRedirects(
            resp,
            "/static/images/favicon.ico",
            status_code=301, target_status_code=404  # @@@ how to avoid 404?
        )

    @override_settings(FAVICON_PATH="images/foo.ico")
    def test_favicon_redirect_with_favicon_path_setting(self):
        self.reset_urls()

        resp = self.client.get("/favicon.ico")
        assert resp.status_code == 301
        self.assertRedirects(
            resp,
            "/static/images/foo.ico",
            status_code=301, target_status_code=404  # @@@ how to avoid 404?
        )
