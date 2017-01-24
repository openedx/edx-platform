"""
Tests for `saml` management command, this command fetches saml metadata from providers and updates
existing data accordingly.
"""
import unittest
import os
import mock

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.conf import settings
from django.utils.six import StringIO

from requests import exceptions
from requests.models import Response

from third_party_auth.tests.factories import SAMLConfigurationFactory, SAMLProviderConfigFactory


def mock_get(status_code=200):
    """
    Args:
        status_code (int): integer showing the status code for the response object.

    Returns:
        returns a function that can be used as a mock function for requests.get.
    """
    def _(url=None, *args, **kwargs):  # pylint: disable=unused-argument
        """
        mock method for requests.get, this method will read xml file, form a Response object from the
        contents of this file, set status code and return the Response object.
        """
        url = url.split("/")[-1] if url else "testshib-providers.xml"

        file_path = os.path.dirname(os.path.realpath(__file__)) + "/test_data/{}".format(url)
        with open(file_path) as providers:
            xml = providers.read()

        response = Response()
        response._content = xml  # pylint: disable=protected-access
        response.status_code = status_code

        return response
    return _


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestSAMLCommand(TestCase):
    """
    Test django management command for fetching saml metadata.
    """
    def setUp(self):
        """
        Setup operations for saml configurations. these operations contain
        creation of SAMLConfiguration and SAMLProviderConfig records in database.
        """
        super(TestSAMLCommand, self).setUp()

        self.stdout = StringIO()

        # We are creating SAMLConfiguration instance here so that there is always at-least one
        # disabled saml configuration instance, this is done to verify that disabled configurations are
        # not processed.
        SAMLConfigurationFactory.create(enabled=False)
        SAMLProviderConfigFactory.create()

    def __create_saml_configurations__(self, saml_config=None, saml_provider_config=None):
        """
        Helper method to create SAMLConfiguration and AMLProviderConfig.
        """
        SAMLConfigurationFactory.create(enabled=True, **(saml_config or {}))
        SAMLProviderConfigFactory.create(enabled=True, **(saml_provider_config or {}))

    def test_raises_command_error_for_invalid_arguments(self):
        """
        Test that management command raises `CommandError` with a proper message in case of
        invalid command arguments.

        This test would fail with an error if ValueError is raised.
        """
        # Call `saml` command without any argument so that it raises a CommandError
        with self.assertRaisesMessage(CommandError, "Command can only be used with '--pull' option."):
            call_command("saml")

        # Call `saml` command without any argument so that it raises a CommandError
        with self.assertRaisesMessage(CommandError, "Command can only be used with '--pull' option."):
            call_command("saml", pull=False)

    def test_no_saml_configuration(self):
        """
        Test that management command completes without errors and logs correct information when no
        saml configurations are enabled/present.
        """
        # Capture command output log for testing.
        call_command("saml", pull=True, stdout=self.stdout)

        self.assertIn('Done. Fetched 0 total. 0 were updated and 0 failed.', self.stdout.getvalue())

    @mock.patch("requests.get", mock_get())
    def test_fetch_saml_metadata(self):
        """
        Test that management command completes without errors and logs correct information when
        one or more saml configurations are enabled.
        """
        # Create enabled configurations
        self.__create_saml_configurations__()

        # Capture command output log for testing.
        call_command("saml", pull=True, stdout=self.stdout)

        self.assertIn('Done. Fetched 1 total. 1 were updated and 0 failed.', self.stdout.getvalue())

    @mock.patch("requests.get", mock_get(status_code=404))
    def test_fetch_saml_metadata_failure(self):
        """
        Test that management command completes with proper message for errors
        and logs correct information.
        """
        # Create enabled configurations
        self.__create_saml_configurations__()

        with self.assertRaisesRegexp(CommandError, r"HTTPError: 404 Client Error"):
            # Capture command output log for testing.
            call_command("saml", pull=True, stdout=self.stdout)

            self.assertIn('Done. Fetched 1 total. 0 were updated and 1 failed.', self.stdout.getvalue())

    @mock.patch("requests.get", mock_get(status_code=200))
    def test_fetch_multiple_providers_data(self):
        """
        Test that management command completes with proper message for error or success
        and logs correct information when there are multiple providers with their data.
        """
        # Create enabled configurations
        self.__create_saml_configurations__()

        # Add another set of configurations
        self.__create_saml_configurations__(
            saml_config={
                "site__domain": "second.testserver.fake",
            },
            saml_provider_config={
                "site__domain": "second.testserver.fake",
                "idp_slug": "second-test-shib",
                "entity_id": "https://idp.testshib.org/idp/another-shibboleth",
                "metadata_source": "https://www.testshib.org/metadata/another-testshib-providers.xml",
            }
        )

        # Add another set of configurations
        self.__create_saml_configurations__(
            saml_config={
                "site__domain": "third.testserver.fake",
            },
            saml_provider_config={
                "site__domain": "third.testserver.fake",
                "idp_slug": "third-test-shib",
                # Note: This entity id will not be present in returned response and will cause failed update.
                "entity_id": "https://idp.testshib.org/idp/non-existent-shibboleth",
                "metadata_source": "https://www.testshib.org/metadata/third/testshib-providers.xml",
            }
        )

        with self.assertRaisesRegexp(CommandError, r"MetadataParseError: Can't find EntityDescriptor for entityID"):
            # Capture command output log for testing.
            call_command("saml", pull=True, stdout=self.stdout)

            self.assertIn('Done. Fetched 3 total. 2 were updated and 1 failed.', self.stdout.getvalue())

    @mock.patch("requests.get")
    def test_saml_request_exceptions(self, mocked_get):
        """
        Test that management command errors out in case of fatal exceptions instead of failing silently.
        """
        # Create enabled configurations
        self.__create_saml_configurations__()

        mocked_get.side_effect = exceptions.SSLError

        with self.assertRaisesRegexp(CommandError, "SSLError:"):
            # Capture command output log for testing.
            call_command("saml", pull=True, stdout=self.stdout)

            self.assertIn('Done. Fetched 1 total. 0 were updated and 1 failed.', self.stdout.getvalue())

        mocked_get.side_effect = exceptions.ConnectionError

        with self.assertRaisesRegexp(CommandError, "ConnectionError:"):
            # Capture command output log for testing.
            call_command("saml", pull=True, stdout=self.stdout)

            self.assertIn('Done. Fetched 1 total. 0 were updated and 1 failed.', self.stdout.getvalue())

        mocked_get.side_effect = exceptions.HTTPError

        with self.assertRaisesRegexp(CommandError, "HTTPError:"):
            # Capture command output log for testing.
            call_command("saml", pull=True, stdout=self.stdout)

            self.assertIn('Done. Fetched 1 total. 0 were updated and 1 failed.', self.stdout.getvalue())

    @mock.patch("requests.get", mock_get(status_code=200))
    def test_saml_parse_exceptions(self):
        """
        Test that management command errors out in case of fatal exceptions instead of failing silently.
        """
        # Create enabled configurations, this configuration will raise MetadataParseError.
        self.__create_saml_configurations__(
            saml_config={
                "site__domain": "third.testserver.fake",
            },
            saml_provider_config={
                "site__domain": "third.testserver.fake",
                "idp_slug": "third-test-shib",
                # Note: This entity id will not be present in returned response and will cause failed update.
                "entity_id": "https://idp.testshib.org/idp/non-existent-shibboleth",
                "metadata_source": "https://www.testshib.org/metadata/third/testshib-providers.xml",
            }
        )

        with self.assertRaisesRegexp(CommandError, "MetadataParseError: Can't find EntityDescriptor for entityID"):
            # Capture command output log for testing.
            call_command("saml", pull=True, stdout=self.stdout)

            self.assertIn('Done. Fetched 1 total. 0 were updated and 1 failed.', self.stdout.getvalue())

    @mock.patch("requests.get")
    def test_xml_parse_exceptions(self, mocked_get):
        """
        Test that management command errors out in case of fatal exceptions instead of failing silently.
        """
        response = Response()
        response._content = ""  # pylint: disable=protected-access
        response.status_code = 200

        mocked_get.return_value = response

        # create enabled configuration
        self.__create_saml_configurations__()

        with self.assertRaisesRegexp(CommandError, "XMLSyntaxError:"):
            # Capture command output log for testing.
            call_command("saml", pull=True, stdout=self.stdout)

            self.assertIn('Done. Fetched 1 total. 0 were updated and 1 failed.', self.stdout.getvalue())
