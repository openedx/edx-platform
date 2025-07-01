"""
Management commands for third_party_auth
"""


import logging

from django.core.management.base import BaseCommand, CommandError

from common.djangoapps.third_party_auth.tasks import fetch_saml_metadata
from common.djangoapps.third_party_auth.models import SAMLProviderConfig, SAMLConfiguration


class Command(BaseCommand):
    """ manage.py commands to manage SAML/Shibboleth SSO """
    help = '''Configure/maintain/update SAML-based SSO'''

    def add_arguments(self, parser):
        parser.add_argument('--pull', action='store_true', help="Pull updated metadata from external IDPs")
        parser.add_argument(
            '--fix-references',
            action='store_true',
            help="Fix SAMLProviderConfig references to use current SAMLConfiguration versions"
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes (use with --fix-references)'
        )
        parser.add_argument(
            '--site-id',
            type=int,
            help='Only fix configurations for a specific site ID (use with --fix-references)'
        )

    def handle(self, *args, **options):
        should_pull_saml_metadata = options.get('pull', False)
        should_fix_references = options.get('fix_references', False)

        if not should_pull_saml_metadata and not should_fix_references:
            raise CommandError("Command must be used with '--pull' or '--fix-references' option.")

        if should_pull_saml_metadata:
            self._handle_pull_metadata()

        if should_fix_references:
            self._handle_fix_references(options)

    def _handle_pull_metadata(self):
        """Handle the --pull option for fetching SAML metadata."""
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

    def _handle_fix_references(self, options):
        """Handle the --fix-references option for fixing outdated SAML configuration references."""
        dry_run = options.get('dry_run', False)
        site_id = options.get('site_id')
        updated_count = 0

        # Filter by site if specified
        provider_configs = SAMLProviderConfig.objects.current_set()
        if site_id:
            provider_configs = provider_configs.filter(site_id=site_id)

        for provider_config in provider_configs:
            if provider_config.saml_configuration:
                try:
                    current_config = SAMLConfiguration.current(
                        provider_config.site_id,
                        provider_config.saml_configuration.slug
                    )

                    if current_config and current_config.id != provider_config.saml_configuration_id:
                        self.stdout.write(
                            f"Provider '{provider_config.slug}' (site {provider_config.site_id}) "
                            f"has outdated config (ID: {provider_config.saml_configuration_id} -> {current_config.id})"
                        )

                        if not dry_run:
                            provider_config.saml_configuration = current_config
                            provider_config.save()

                        updated_count += 1

                except Exception as e:  # pylint: disable=broad-except
                    self.stderr.write(
                        f"Error processing provider '{provider_config.slug}': {e}"
                    )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"Would update {updated_count} provider configurations")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Updated {updated_count} provider configurations")
            )
