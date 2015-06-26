# -*- coding: utf-8 -*-
"""
Management commands for third_party_auth
"""
from django.core.management.base import BaseCommand, CommandError
import logging
from third_party_auth.models import SAMLConfiguration
from third_party_auth.tasks import fetch_saml_metadata


class Command(BaseCommand):
    """ manage.py commands to manage SAML/Shibboleth SSO """
    help = '''Configure/maintain/update SAML-based SSO'''

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("saml requires one argument: pull")

        if not SAMLConfiguration.is_enabled():
            raise CommandError("SAML support is disabled via SAMLConfiguration.")

        subcommand = args[0]

        if subcommand == "pull":
            log_handler = logging.StreamHandler(self.stdout)
            log_handler.setLevel(logging.DEBUG)
            log = logging.getLogger('third_party_auth.tasks')
            log.propagate = False
            log.addHandler(log_handler)
            num_changed, num_failed, num_total = fetch_saml_metadata()
            self.stdout.write(
                "\nDone. Fetched {num_total} total. {num_changed} were updated and {num_failed} failed.\n".format(
                    num_changed=num_changed, num_failed=num_failed, num_total=num_total
                )
            )
        else:
            raise CommandError("Unknown argment: {}".format(subcommand))
