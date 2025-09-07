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
        parser.add_argument(
            '--site-id',
            type=int,
            help='Only check configurations for a specific site ID (to be used with --run-checks)'
        )

    def handle(self, *args, **options):
        should_pull_saml_metadata = options.get('pull', False)
        should_run_checks = options.get('run_checks', False)

        if not should_pull_saml_metadata and not should_run_checks:
            raise CommandError("Command must be used with '--pull' or '--run-checks' option.")

        if should_pull_saml_metadata:
            self._handle_pull_metadata()

        if should_run_checks:
            self._handle_run_checks(options)

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

    def _handle_run_checks(self, options):
        """
        Handle the --run-checks option for checking SAML configuration issues.

        This is a report-only command that identifies potential configuration problems:
        - Outdated configuration references
        - Site ID mismatches between provider and configuration
        - Slug mismatches (except when slug is 'default' which may be intentional)
        - Providers with null configurations (informational)

        Includes observability attributes for monitoring.
        """
        site_id = options.get('site_id')

        # .. custom_attribute_name: saml_management_command.operation
        # .. custom_attribute_description: Records the operation being performed by the management command.
        set_custom_attribute('saml_management_command.operation', 'run_checks')

        # .. custom_attribute_name: saml_management_command.site_filter
        # .. custom_attribute_description: Records the site filter applied, either specific site ID or 'all'.
        set_custom_attribute('saml_management_command.site_filter', str(site_id) if site_id else 'all')

        outdated_count = 0
        site_mismatch_count = 0
        slug_mismatch_count = 0
        null_config_count = 0
        error_count = 0
        total_providers = 0

        provider_configs = SAMLProviderConfig.objects.current_set()
        if site_id:
            provider_configs = provider_configs.filter(site_id=site_id)

        self.stdout.write(self.style.SUCCESS("SAML Configuration Check Report"))
        self.stdout.write("=" * 50)

        for provider_config in provider_configs:
            total_providers += 1
            provider_info = f"Provider '{provider_config.slug}' (site {provider_config.site_id})"

            if not provider_config.saml_configuration:
                self.stdout.write(f"[INFO] {provider_info} has no SAML configuration (may be intentional)")
                null_config_count += 1
                continue

            try:
                current_config = SAMLConfiguration.current(
                    provider_config.site_id,
                    provider_config.saml_configuration.slug
                )

                # Check for outdated configuration references
                if current_config and current_config.id != provider_config.saml_configuration_id:
                    self.stdout.write(
                        f"[OUTDATED] {provider_info} "
                        f"has outdated config (ID: {provider_config.saml_configuration_id} -> {current_config.id})"
                    )
                    outdated_count += 1

                if provider_config.saml_configuration.site_id != provider_config.site_id:
                    self.stdout.write(
                        f"[SITE_MISMATCH] {provider_info} "
                        f"config site ({provider_config.saml_configuration.site_id}) != provider site ({provider_config.site_id})"
                    )
                    site_mismatch_count += 1

                actual_slug = provider_config.saml_configuration.slug
                expected_slug = provider_config.slug
                if (actual_slug != expected_slug and
                        actual_slug != 'default' and
                        expected_slug != 'default'):
                    self.stdout.write(
                        f"[SLUG_MISMATCH] {provider_info} "
                        f"config slug ('{actual_slug}') != provider slug ('{expected_slug}')"
                    )
                    slug_mismatch_count += 1

            except Exception as e:  # pylint: disable=broad-except
                self.stderr.write(f"[ERROR] Error processing {provider_info}: {e}")
                error_count += 1

        metrics = {
            'total_providers': total_providers,
            'outdated_count': outdated_count,
            'site_mismatch_count': site_mismatch_count,
            'slug_mismatch_count': slug_mismatch_count,
            'null_config_count': null_config_count,
            'error_count': error_count,
        }

        for key, value in metrics.items():
            # .. custom_attribute_name: saml_management_command.{key}
            # .. custom_attribute_description: Records metrics from SAML configuration checks.
            set_custom_attribute(f'saml_management_command.{key}', value)

        total_issues = outdated_count + site_mismatch_count + slug_mismatch_count

        # .. custom_attribute_name: saml_management_command.total_issues
        # .. custom_attribute_description: The total number of configuration issues requiring attention.
        set_custom_attribute('saml_management_command.total_issues', total_issues)

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("CHECK SUMMARY:"))
        self.stdout.write(f"  Providers: {total_providers}")
        self.stdout.write(f"  Outdated: {outdated_count}")
        self.stdout.write(f"  Site mismatches: {site_mismatch_count}")
        self.stdout.write(f"  Slug mismatches: {slug_mismatch_count}")
        self.stdout.write(f"  Null configs: {null_config_count}")
        self.stdout.write(f"  Errors: {error_count}")

        if total_issues > 0:
            self.stdout.write(f"\nTotal issues requiring attention: {total_issues}")
        else:
            self.stdout.write(self.style.SUCCESS("\nNo configuration issues found!"))
