# -*- coding: utf-8 -*-
"""
Management commands for third_party_auth
"""
from django.core.management.base import BaseCommand, CommandError
import logging
from third_party_auth.tasks import fetch_saml_metadata


class Command(BaseCommand):
    """ manage.py commands to manage SAML/Shibboleth SSO """
    help = '''Configure/maintain/update SAML-based SSO'''

    def add_arguments(self, parser):
        parser.add_argument('--pull', action='store_true', help="Pull updated metadata from external IDPs")

    def handle(self, *args, **options):
        should_pull_saml_metadata = options.get('pull', False)

        if not should_pull_saml_metadata:
            raise CommandError("Command can only be used with '--pull' option.")

        log_handler = logging.StreamHandler(self.stdout)
        log_handler.setLevel(logging.DEBUG)
        log = logging.getLogger('third_party_auth.tasks')
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
