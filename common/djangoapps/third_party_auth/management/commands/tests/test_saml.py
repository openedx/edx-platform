"""
Tests for `saml` management command, this command fetches saml metadata from providers and updates
existing data accordingly.
"""


import os
from io import StringIO

from unittest import mock
from ddt import ddt
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.management.base import CommandError
from requests import exceptions
from requests.models import Response

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from common.djangoapps.third_party_auth.tests.factories import SAMLConfigurationFactory, SAMLProviderConfigFactory


def mock_get(status_code=200):
    """
    Args:
        status_code (int): integer showing the status code for the response object.

    Returns:
        returns a function that can be used as a mock function for requests.get.
    """
    def _(url=None, *args, **kwargs):  # lint-amnesty, pylint: disable=keyword-arg-before-vararg, unused-argument
        """
        mock method for requests.get, this method will read xml file, form a Response object from the
        contents of this file, set status code and return the Response object.
        """
        url = url.split("/")[-1] if url else "testshib-providers.xml"

        file_path = os.path.dirname(os.path.realpath(__file__)) + f"/test_data/{url}"
        with open(file_path) as providers:
            xml = providers.read()

        response = Response()
        response._content = xml  # pylint: disable=protected-access
        response.status_code = status_code

        return response
    return _


@skip_unless_lms
@ddt
class TestSAMLCommand(CacheIsolationTestCase):
    """
    Test django management command for fetching saml metadata.
    """

    def setUp(self):
        """
        Setup operations for saml configurations. these operations contain
        creation of SAMLConfiguration and SAMLProviderConfig records in database.
        """
        super().setUp()

        self.stdout = StringIO()
        self.site = Site.objects.get_current()
        self.other_site = Site.objects.create(domain='other.example.com', name='Other Site')

        # We are creating SAMLConfiguration instance here so that there is always at-least one
        # disabled saml configuration instance, this is done to verify that disabled configurations are
        # not processed.
        self.saml_config = SAMLConfigurationFactory.create(
            enabled=False,
            site__domain='testserver.fake',
            site__name='testserver.fake'
        )
        self.provider_config = SAMLProviderConfigFactory.create(
            site__domain='testserver.fake',
            site__name='testserver.fake',
            slug='test-shib',
            name='TestShib College',
            entity_id='https://idp.testshib.org/idp/shibboleth',
            metadata_source='https://www.testshib.org/metadata/testshib-providers.xml',
        )

    def _setup_test_configs_for_run_checks(self):
        """
        Helper method to create SAML configurations for run-checks tests.

        Returns tuple of (old_config, new_config, provider_config)

        Using a separate method keeps test data isolated. Including these configs in
        setUp would create 3 provider configs for all tests, breaking tests that expect
        specific provider counts or try to access non-existent test XML files.
        """
        # Create a SAML config that will be outdated after the new config is created
        old_config = SAMLConfigurationFactory.create(
            enabled=False,
            site=self.site,
            slug='test-config',
            entity_id='https://old.example.com'
        )

        # Create newer config with same slug
        new_config = SAMLConfigurationFactory.create(
            enabled=True,
            site=self.site,
            slug='test-config',
            entity_id='https://updated.example.com'
        )

        # Create a provider config that references the old config for run-checks tests
        test_provider_config = SAMLProviderConfigFactory.create(
            site=self.site,
            slug='test-provider',
            name='Test Provider',
            entity_id='https://test.provider/idp/shibboleth',
            metadata_source='https://test.provider/metadata.xml',
            saml_configuration=old_config
        )

        return old_config, new_config, test_provider_config

    def __create_saml_configurations__(self, saml_config=None, saml_provider_config=None):
        """
        Helper method to create SAMLConfiguration and AMLProviderConfig.
        """
        SAMLConfigurationFactory.create(enabled=True, **(
            saml_config or {
                'site__domain': 'testserver.fake',
                'site__name': 'testserver.fake',
            }
        ))
        SAMLProviderConfigFactory.create(enabled=True, **(
            saml_provider_config or {
                'site__domain': 'testserver.fake',
                'site__name': 'testserver.fake',
                'slug': 'test-shib',
                'name': 'TestShib College',
                'entity_id': 'https://idp.testshib.org/idp/shibboleth',
                'metadata_source': 'https://www.testshib.org/metadata/testshib-providers.xml',
            }
        ))

    def test_raises_command_error_for_invalid_arguments(self):
        """
        Test that management command raises `CommandError` with a proper message in case of
        invalid command arguments.

        This test would fail with an error if ValueError is raised.
        """
        # Call `saml` command without any arguments so that it raises a CommandError
        with self.assertRaisesMessage(CommandError, "Command must be used with '--pull' or '--run-checks' option."):
            call_command("saml")

    def test_no_saml_configuration(self):
        """
        Test that management command completes without errors and logs correct information when no
        saml configurations are enabled/present.
        """
        expected = "\nDone.\n1 provider(s) found in database.\n1 skipped and 0 attempted.\n0 updated and 0 failed.\n"
        call_command("saml", pull=True, stdout=self.stdout)
        assert expected in self.stdout.getvalue()

    @mock.patch("requests.get", mock_get())
    def test_fetch_saml_metadata(self):
        """
        Test that management command completes without errors and logs correct information when
        one or more saml configurations are enabled.
        """
        # Create enabled configurations
        self.__create_saml_configurations__()

        expected = "\nDone.\n1 provider(s) found in database.\n0 skipped and 1 attempted.\n1 updated and 0 failed.\n"
        call_command("saml", pull=True, stdout=self.stdout)
        assert expected in self.stdout.getvalue()

    @mock.patch("requests.get", mock_get(status_code=404))
    def test_fetch_saml_metadata_failure(self):
        """
        Test that management command completes with proper message for errors
        and logs correct information.
        """
        # Create enabled configurations
        self.__create_saml_configurations__()

        expected = "\nDone.\n1 provider(s) found in database.\n0 skipped and 1 attempted.\n0 updated and 1 failed.\n"

        with self.assertRaisesRegex(CommandError, r"HTTPError: 404 Client Error"):
            call_command("saml", pull=True, stdout=self.stdout)
        assert expected in self.stdout.getvalue()

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
                "site__name": "testserver.fake",
            },
            saml_provider_config={
                "site__domain": "second.testserver.fake",
                "site__name": "testserver.fake",
                "slug": "second-test-shib",
                "entity_id": "https://idp.testshib.org/idp/another-shibboleth",
                "metadata_source": "https://www.testshib.org/metadata/another-testshib-providers.xml",
            }
        )

        # Add another set of configurations
        self.__create_saml_configurations__(
            saml_config={
                "site__domain": "third.testserver.fake",
                "site__name": "testserver.fake",
            },
            saml_provider_config={
                "site__domain": "third.testserver.fake",
                "site__name": "testserver.fake",
                "slug": "third-test-shib",
                # Note: This entity id will not be present in returned response and will cause failed update.
                "entity_id": "https://idp.testshib.org/idp/non-existent-shibboleth",
                "metadata_source": "https://www.testshib.org/metadata/third/testshib-providers.xml",
            }
        )

        expected = '\n3 provider(s) found in database.\n0 skipped and 3 attempted.\n2 updated and 1 failed.\n'
        with self.assertRaisesRegex(CommandError, r"MetadataParseError: Can't find EntityDescriptor for entityID"):
            call_command("saml", pull=True, stdout=self.stdout)
        assert expected in self.stdout.getvalue()

        # Now add a fourth configuration, and indicate that it should not be included in the update
        self.__create_saml_configurations__(
            saml_config={
                "site__domain": "fourth.testserver.fake",
                "site__name": "testserver.fake",
            },
            saml_provider_config={
                "site__domain": "fourth.testserver.fake",
                "site__name": "testserver.fake",
                "slug": "fourth-test-shib",
                "automatic_refresh_enabled": False,
                # Note: This invalid entity id will not be present in the refresh set
                "entity_id": "https://idp.testshib.org/idp/fourth-shibboleth",
                "metadata_source": "https://www.testshib.org/metadata/fourth/testshib-providers.xml",
            }
        )

        # Four configurations -- one will be skipped and three attempted, with similar results.
        expected = '\nDone.\n4 provider(s) found in database.\n1 skipped and 3 attempted.\n0 updated and 1 failed.\n'
        with self.assertRaisesRegex(CommandError, r"MetadataParseError: Can't find EntityDescriptor for entityID"):
            call_command("saml", pull=True, stdout=self.stdout)
        assert expected in self.stdout.getvalue()

    @mock.patch("requests.get")
    def test_saml_request_exceptions(self, mocked_get):
        """
        Test that management command errors out in case of fatal exceptions instead of failing silently.
        """
        # Create enabled configurations
        self.__create_saml_configurations__()

        mocked_get.side_effect = exceptions.SSLError

        expected = "\nDone.\n1 provider(s) found in database.\n0 skipped and 1 attempted.\n0 updated and 1 failed.\n"

        with self.assertRaisesRegex(CommandError, "SSLError:"):
            call_command("saml", pull=True, stdout=self.stdout)
        assert expected in self.stdout.getvalue()

        mocked_get.side_effect = exceptions.ConnectionError

        with self.assertRaisesRegex(CommandError, "ConnectionError:"):
            call_command("saml", pull=True, stdout=self.stdout)
        assert expected in self.stdout.getvalue()

        mocked_get.side_effect = exceptions.HTTPError

        with self.assertRaisesRegex(CommandError, "HTTPError:"):
            call_command("saml", pull=True, stdout=self.stdout)
        assert expected in self.stdout.getvalue()

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
                "slug": "third-test-shib",
                # Note: This entity id will not be present in returned response and will cause failed update.
                "entity_id": "https://idp.testshib.org/idp/non-existent-shibboleth",
                "metadata_source": "https://www.testshib.org/metadata/third/testshib-providers.xml",
            }
        )

        expected = "\nDone.\n2 provider(s) found in database.\n1 skipped and 1 attempted.\n0 updated and 1 failed.\n"

        with self.assertRaisesRegex(CommandError, "MetadataParseError: Can't find EntityDescriptor for entityID"):
            call_command("saml", pull=True, stdout=self.stdout)
        assert expected in self.stdout.getvalue()

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

        expected = "\nDone.\n1 provider(s) found in database.\n0 skipped and 1 attempted.\n0 updated and 1 failed.\n"

        with self.assertRaisesRegex(CommandError, "XMLSyntaxError:"):
            call_command("saml", pull=True, stdout=self.stdout)
        assert expected in self.stdout.getvalue()

    def _run_checks_command(self):
        """
        Helper method to run the --run-checks command and return output.
        """
        out = StringIO()
        call_command('saml', '--run-checks', stdout=out)
        return out.getvalue()

    @mock.patch('common.djangoapps.third_party_auth.management.commands.saml.set_custom_attribute')
    def test_run_checks_outdated_configs(self, mock_set_custom_attribute):
        """
        Test the --run-checks command identifies outdated configurations.
        """
        old_config, new_config, test_provider_config = self._setup_test_configs_for_run_checks()

        output = self._run_checks_command()

        self.assertIn('[WARNING]', output)
        self.assertIn('test-provider', output)
        self.assertIn(
            f'id={old_config.id} which should be updated to the current SAML config (id={new_config.id})',
            output
        )
        self.assertIn('CHECK SUMMARY:', output)
        self.assertIn('Providers checked: 2', output)
        self.assertIn('Outdated: 1', output)

        # Check key observability calls
        expected_calls = [
            mock.call('saml_management_command.operation', 'run_checks'),
            mock.call('saml_management_command.total_providers', 2),
            mock.call('saml_management_command.outdated_count', 1),
            mock.call('saml_management_command.site_mismatch_count', 0),
            mock.call('saml_management_command.slug_mismatch_count', 1),
            mock.call('saml_management_command.null_config_count', 1),
            mock.call('saml_management_command.error_count', 0),
            mock.call('saml_management_command.total_requiring_attention', 2),
        ]
        mock_set_custom_attribute.assert_has_calls(expected_calls, any_order=False)

    @mock.patch('common.djangoapps.third_party_auth.management.commands.saml.set_custom_attribute')
    def test_run_checks_site_mismatches(self, mock_set_custom_attribute):
        """
        Test the --run-checks command identifies site ID mismatches.
        """
        config = SAMLConfigurationFactory.create(
            site=self.other_site,
            slug='test-config',
            entity_id='https://example.com'
        )

        SAMLProviderConfigFactory.create(
            site=self.site,
            slug='test-provider',
            saml_configuration=config
        )

        output = self._run_checks_command()

        self.assertIn('[WARNING]', output)
        self.assertIn('test-provider', output)
        self.assertIn('does not match the provider\'s site_id', output)

        # Check observability calls
        expected_calls = [
            mock.call('saml_management_command.operation', 'run_checks'),
            mock.call('saml_management_command.total_providers', 2),
            mock.call('saml_management_command.outdated_count', 0),
            mock.call('saml_management_command.site_mismatch_count', 1),
            mock.call('saml_management_command.slug_mismatch_count', 1),
            mock.call('saml_management_command.null_config_count', 1),
            mock.call('saml_management_command.error_count', 0),
            mock.call('saml_management_command.total_requiring_attention', 2),
        ]
        mock_set_custom_attribute.assert_has_calls(expected_calls, any_order=False)

    @mock.patch('common.djangoapps.third_party_auth.management.commands.saml.set_custom_attribute')
    def test_run_checks_slug_mismatches(self, mock_set_custom_attribute):
        """
        Test the --run-checks command identifies slug mismatches.
        """
        config = SAMLConfigurationFactory.create(
            site=self.site,
            slug='config-slug',
            entity_id='https://example.com'
        )

        SAMLProviderConfigFactory.create(
            site=self.site,
            slug='provider-slug',
            saml_configuration=config
        )

        output = self._run_checks_command()

        self.assertIn('[WARNING]', output)
        self.assertIn('provider-slug', output)
        self.assertIn('does not match the provider\'s slug', output)

        # Check observability calls
        expected_calls = [
            mock.call('saml_management_command.operation', 'run_checks'),
            mock.call('saml_management_command.total_providers', 2),
            mock.call('saml_management_command.outdated_count', 0),
            mock.call('saml_management_command.site_mismatch_count', 0),
            mock.call('saml_management_command.slug_mismatch_count', 1),
            mock.call('saml_management_command.null_config_count', 1),
            mock.call('saml_management_command.error_count', 0),
            mock.call('saml_management_command.total_requiring_attention', 1),
        ]
        mock_set_custom_attribute.assert_has_calls(expected_calls, any_order=False)

    @mock.patch('common.djangoapps.third_party_auth.management.commands.saml.set_custom_attribute')
    def test_run_checks_null_configurations(self, mock_set_custom_attribute):
        """
        Test the --run-checks command identifies providers with null configurations.
        """
        SAMLProviderConfigFactory.create(
            site=self.site,
            slug='null-provider',
            saml_configuration=None
        )

        output = self._run_checks_command()

        self.assertIn('[INFO]', output)
        self.assertIn('null-provider', output)
        self.assertIn('has no SAML configuration because a matching default was not found', output)

        # Check observability calls
        expected_calls = [
            mock.call('saml_management_command.operation', 'run_checks'),
            mock.call('saml_management_command.total_providers', 2),
            mock.call('saml_management_command.outdated_count', 0),
            mock.call('saml_management_command.site_mismatch_count', 0),
            mock.call('saml_management_command.slug_mismatch_count', 0),
            mock.call('saml_management_command.null_config_count', 2),
            mock.call('saml_management_command.error_count', 0),
            mock.call('saml_management_command.total_requiring_attention', 0),
        ]
        mock_set_custom_attribute.assert_has_calls(expected_calls, any_order=False)
