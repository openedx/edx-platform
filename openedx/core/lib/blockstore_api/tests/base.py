"""
Common code for tests that work with Blockstore
"""
from unittest import mock
from urllib.parse import urlparse

from django.test.client import RequestFactory


class BlockstoreAppTestMixin:
    """
    Sets up the environment for tests to be run using the installed Blockstore app.
    """
    def setUp(self):
        """
        Ensure there's an active request, so that bundle file URLs can be made absolute.
        """
        super().setUp()

        # Patch the blockstore get_current_request to use our live_server_url
        mock.patch('blockstore.apps.api.methods.get_current_request',
                   mock.Mock(return_value=self._get_current_request())).start()
        self.addCleanup(mock.patch.stopall)

    def _get_current_request(self):
        """
        Returns a request object using the live_server_url, if available.
        """
        request_args = {}
        if hasattr(self, 'live_server_url'):
            live_server_url = urlparse(self.live_server_url)
            name, port = live_server_url.netloc.split(':')
            request_args['SERVER_NAME'] = name
            request_args['SERVER_PORT'] = port or '80'
            request_args['wsgi.url_scheme'] = live_server_url.scheme
        return RequestFactory().request(**request_args)
