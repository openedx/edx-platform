"""
Management commands for third_party_auth
"""


import logging

from django.core.management.base import BaseCommand, CommandError
from edx_django_utils.monitoring import set_custom_attribute

from common.djangoapps.third_party_auth.tasks import fetch_saml_metadata
from common.djangoapps.third_party_auth.models import SAMLProviderConfig, SAMLConfiguration


class Command(BaseCommand):
    """ manage.py commands to manage SAML/Shibboleth SSO """
    help = '''Configure/maintain/update SAML-based SSO'''

    def add_arguments(self, parser):
        parser.add_argument('--pull', action='store_true', help="Pull updated metadata from external IDPs")
        parser.add_argument(
            '--run-checks',
            action='store_true',
            help="Run checks on SAMLProviderConfig configurations and report potential issues"
        )

    def handle(self, *args, **options):
        should_pull_saml_metadata = options.get('pull', False)
        should_run_checks = options.get('run_checks', False)

        if should_pull_saml_metadata:
            self._handle_pull_metadata()
            return

        if should_run_checks:
            self._handle_run_checks()
            return

        raise CommandError("Command must be used with '--pull' or '--run-checks' option.")

    def _handle_pull_metadata(self):
        """
        Handle the --pull option to fetch and update SAML metadata from external providers.
        This sets up logging and calls the fetch_saml_metadata task.
        """
        log_handler = logging.StreamHandler(self.stdout)
        log_handler.setLevel(logging.DEBUG)
        log = logging.getLogger('common.djangoapps.third_party_auth.tasks')
        log.propagate = False
        log.addHandler(log_handler)
        total, skipped, attempted, updated, failed, failure_messages = fetch_saml_metadata()
        self.stdout.write(
            "\nDone."
            "\n{total} provider(s) found in database."
            "\n{skipped} skipped and {attempted} attempted."
            "\n{updated} updated and {failed} failed.\n".format(
                total=total,
                skipped=skipped, attempted=attempted,
                updated=updated, failed=failed,
            )
        )

        if failed > 0:
            raise CommandError(
                "Command finished with the following exceptions:\n\n{failures}".format(
                    failures="\n\n".join(failure_messages)
                )
            )

    def _handle_run_checks(self):
        """
        Handle the --run-checks option for checking SAMLProviderConfig configuration issues.

        This is a report-only command. It identifies potential configuration problems such as:
        - Outdated SAMLConfiguration references (provider pointing to old config version)
        - Site ID mismatches between SAMLProviderConfig and its SAMLConfiguration
        - Slug mismatches (except 'default' slugs)  # noqa: E501
        - SAMLProviderConfig objects with no available configuration (no direct config AND no default)

        Uses get_config() to accurately determine if a provider has usable configuration,
        eliminating false warnings for providers that correctly use default configurations.

        Includes observability attributes for monitoring.
        """
        # Set custom attributes for monitoring the check operation
        # .. custom_attribute_name: saml_management_command.operation
        # .. custom_attribute_description: Records current SAML operation ('run_checks').
        set_custom_attribute('saml_management_command.operation', 'run_checks')

        metrics = self._check_provider_configurations()
        self._report_check_summary(metrics)

    def _check_provider_configurations(self):
        """
        Check each provider configuration for potential issues.
        Returns a dictionary of metrics about the found issues.
        """
        outdated_count = 0
        site_mismatch_count = 0
        slug_mismatch_count = 0
        null_config_count = 0
        error_count = 0
        total_providers = 0

        provider_configs = SAMLProviderConfig.objects.current_set()

        self.stdout.write(self.style.SUCCESS("SAML Configuration Check Report"))
        self.stdout.write("=" * 50)
        self.stdout.write("")

        for provider_config in provider_configs:
            total_providers += 1
            provider_info = (
                f"Provider (id={provider_config.id}, name={provider_config.name}, "
                f"slug={provider_config.slug}, site_id={provider_config.site_id})"
            )

            try:
                # Use get_config() to get the actual configuration that would be used
                # This includes both direct configuration and default fallback logic
                actual_config = provider_config.get_config()
   
                if not actual_config:
                    self.stdout.write(
                        f"[WARNING] {provider_info} has no SAML configuration and "
                        "no matching default configuration was found."
                    )
                    null_config_count += 1
                    continue

                if provider_config.saml_configuration:
                    current_config = SAMLConfiguration.current(
                        provider_config.saml_configuration.site_id,
                        provider_config.saml_configuration.slug
                    )

                    if current_config and current_config.id != provider_config.saml_configuration_id:
                        self.stdout.write(
                            f"[WARNING] {provider_info} "
                            f"has outdated SAML config (id={provider_config.saml_configuration_id}) which "
                            f"should be updated to the current SAML config (id={current_config.id})."
                        )
                        outdated_count += 1

                    if provider_config.saml_configuration.site_id != provider_config.site_id:
                        config_site_id = provider_config.saml_configuration.site_id
                        self.stdout.write(
                            f"[WARNING] {provider_info} "
                            f"SAML config (id={provider_config.saml_configuration_id}, site_id={config_site_id}) "
                            "does not match the provider's site_id."
                        )
                        site_mismatch_count += 1

                    saml_configuration_slug = provider_config.saml_configuration.slug
                    provider_config_slug = provider_config.slug

                    if saml_configuration_slug not in (provider_config_slug, 'default'):
                        self.stdout.write(
                            f"[WARNING] {provider_info} "
                            f"SAML config (id={provider_config.saml_configuration_id}, slug='{saml_configuration_slug}') "
                            "does not match the provider's slug."
                        )
                        slug_mismatch_count += 1

            except Exception as e:  # pylint: disable=broad-except
                self.stderr.write(f"[ERROR] Error processing {provider_info}: {e}")
                error_count += 1

        metrics = {
            'total_providers': {'count': total_providers, 'requires_attention': False},
            'outdated_count': {'count': outdated_count, 'requires_attention': True},
            'site_mismatch_count': {'count': site_mismatch_count, 'requires_attention': True},
            'slug_mismatch_count': {'count': slug_mismatch_count, 'requires_attention': True},
            'null_config_count': {'count': null_config_count, 'requires_attention': True},
            'error_count': {'count': error_count, 'requires_attention': True},
        }

        for key, metric_data in metrics.items():
            # .. custom_attribute_name: saml_management_command.{key}
            # .. custom_attribute_description: Records metrics from SAML configuration checks.
            set_custom_attribute(f'saml_management_command.{key}', metric_data['count'])

        return metrics

    def _report_check_summary(self, metrics):
        """
        Print a summary of the check results and set the total_requiring_attention custom attribute.
        """
        total_requiring_attention = sum(
            metric_data['count'] for metric_data in metrics.values()
            if metric_data['requires_attention']
        )

        # .. custom_attribute_name: saml_management_command.total_requiring_attention
        # .. custom_attribute_description: The total number of configuration issues requiring attention.
        set_custom_attribute('saml_management_command.total_requiring_attention', total_requiring_attention)

        self.stdout.write(self.style.SUCCESS("CHECK SUMMARY:"))
        self.stdout.write(f"  Providers checked: {metrics['total_providers']['count']}")
        self.stdout.write(f"  Missing configs: {metrics['null_config_count']['count']}")

        if total_requiring_attention > 0:
            self.stdout.write("\nIssues requiring attention:")
            self.stdout.write(f"  Outdated: {metrics['outdated_count']['count']}")
            self.stdout.write(f"  Site mismatches: {metrics['site_mismatch_count']['count']}")
            self.stdout.write(f"  Slug mismatches: {metrics['slug_mismatch_count']['count']}")
            self.stdout.write(f"  Missing configs: {metrics['null_config_count']['count']}")
            self.stdout.write(f"  Errors: {metrics['error_count']['count']}")
            self.stdout.write(f"\nTotal issues requiring attention: {total_requiring_attention}")
        else:
            self.stdout.write(self.style.SUCCESS("\nNo configuration issues found!"))
