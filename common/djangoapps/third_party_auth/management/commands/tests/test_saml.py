"""
Tests for `saml` management command, this command fetches saml metadata from providers and updates
existing data accordingly.
"""


import os
from io import StringIO

from unittest import mock
from ddt import ddt, data, unpack
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.management.base import CommandError
from requests import exceptions
from requests.models import Response

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from common.djangoapps.third_party_auth.tests.factories import SAMLConfigurationFactory, SAMLProviderConfigFactory


from common.djangoapps.third_party_auth.models import SAMLConfiguration, SAMLProviderConfig


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

        # We are creating SAMLConfiguration instance here so that there is always at-least one
        # disabled saml configuration instance, this is done to verify that disabled configurations are
        # not processed.
        self.saml_config = SAMLConfigurationFactory.create(enabled=False, site__domain='testserver.fake', site__name='testserver.fake')
        self.provider_config = SAMLProviderConfigFactory.create(
            site__domain='testserver.fake',
            site__name='testserver.fake',
            slug='test-shib',
            name='TestShib College',
            entity_id='https://idp.testshib.org/idp/shibboleth',
            metadata_source='https://www.testshib.org/metadata/testshib-providers.xml',
        )

    def _setup_test_configs(self):
        """
        Helper method to create SAML configurations for fix-references tests.
        Returns tuple of (old_config, new_config, provider_config)

        Using a separate method keeps test data isolated. Including these configs in
        setUp would create 3 provider configs for all tests, breaking tests that expect
        specific provider counts or try to access non-existent test XML files.
        """
        # Create an old SAML config for testing fix-references functionality
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

        # Create a provider config that references the old config for fix-references tests
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
        # Call `saml` command without any argument so that it raises a CommandError
        with self.assertRaisesMessage(CommandError, "Command must be used with '--pull' or '--fix-references' option."):
            call_command("saml")

        # Call `saml` command without any argument so that it raises a CommandError
        with self.assertRaisesMessage(CommandError, "Command must be used with '--pull' or '--fix-references' option."):
            call_command("saml", pull=False)

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

    @data(
        (True, '[DRY RUN]', 'should not update provider configs'),
        (False, '', 'should create new provider config for new version')
    )
    @unpack
    def test_fix_references(self, dry_run, expected_output_marker, test_description):
        """
        Test the --fix-references command with and without --dry-run option.

        Args:
            dry_run (bool): Whether to run with --dry-run flag
            expected_output_marker (str): Expected marker in output
            test_description (str): Description of what the test should do
        """
        old_config, new_config, test_provider_config = self._setup_test_configs()
        new_config_id = new_config.id
        original_config_id = old_config.id

        out = StringIO()
        if dry_run:
            call_command('saml', '--fix-references', '--dry-run', stdout=out)
        else:
            call_command('saml', '--fix-references', stdout=out)

        output = out.getvalue()

        self.assertIn('test-provider', output)
        if expected_output_marker:
            self.assertIn(expected_output_marker, output)

        test_provider_config.refresh_from_db()

        if dry_run:
            # For dry run, ensure the provider config was NOT updated
            self.assertEqual(
                test_provider_config.saml_configuration_id,
                original_config_id,
                "Provider config should not be updated in dry run mode"
            )
        else:
            # For actual run, check that a new provider config was created
            new_provider = SAMLProviderConfig.objects.filter(
                site=self.site,
                slug='test-provider',
                saml_configuration_id=new_config_id
            ).exclude(id=test_provider_config.id).first()

            self.assertIsNotNone(new_provider, "New provider config should be created")
            self.assertEqual(new_provider.saml_configuration_id, new_config_id)

            # Original provider config should still reference the old config
            self.assertEqual(
                test_provider_config.saml_configuration_id,
                original_config_id,
                "Original provider config should still reference old config"
            )
