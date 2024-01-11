"""Tests for remote_exec.py"""

import unittest

import ddt
import requests
from django.test import override_settings
from edx_rest_api_client.client import OAuthAPIClient

from xmodule.capa.safe_exec import remote_exec


@ddt.ddt
class RemoteExecTest(unittest.TestCase):
    """Tests for remote execution."""

    # pylint: disable=protected-access
    @ddt.unpack
    @ddt.data(
        ({}, False),
        # If just one or two settings present, skip auth
        ({'CODE_JAIL_REST_SERVICE_OAUTH_URL': 'https://oauth.localhost'}, False),
        (
            {
                'CODE_JAIL_REST_SERVICE_OAUTH_CLIENT_ID': 'some-id',
                'CODE_JAIL_REST_SERVICE_OAUTH_CLIENT_SECRET': 'some-key'
            },
            False,
        ),
        # Configure auth if all present
        (
            {
                'CODE_JAIL_REST_SERVICE_OAUTH_URL': 'https://oauth.localhost',
                'CODE_JAIL_REST_SERVICE_OAUTH_CLIENT_ID': 'some-id',
                'CODE_JAIL_REST_SERVICE_OAUTH_CLIENT_SECRET': 'some-key',
            },
            True,
        ),
    )
    def test_auth_config(self, settings, expect_auth):
        """
        Check if the correct client is selected based on configuration.
        """
        with override_settings(**settings):
            if expect_auth:
                assert isinstance(remote_exec._get_codejail_client(), OAuthAPIClient)
            else:
                # Don't actually care that it's the requests module specifically,
                # just that it's something generic and unconfigured for auth.
                assert remote_exec._get_codejail_client() is requests
