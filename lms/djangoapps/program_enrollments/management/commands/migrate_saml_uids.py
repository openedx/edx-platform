"""
Management command to re-write UIDs identifying learners in external organizations' systems

Intented for use in production environments, to help support migration
of existing SSO learners into our most-recent program enrollment flow
without needing to manually re-link their account.
"""
from __future__ import absolute_import, unicode_literals

import json
import logging
from io import open
from textwrap import dedent

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Updates UserSocialAuth records to use UIDs provided in the supplied JSON file

    Example usage:
        $ ./manage.py lms migrate_saml_uids.py \
          --uid-mapping=path/to/file.json
          --saml-provider-slug=default
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        parser.add_argument(
            '--uid-mapping',
            help='path to utf-8-encoded json file containing an array of objects with keys email and student_key'
        )
        parser.add_argument(
            '--saml-provider-slug',
            help='slug of SAMLProvider for which records should be updated'
        )

    def handle(self, *args, **options):
        """
        Performs the re-writing
        """
        User = get_user_model()
        with open(options['uid_mapping'], 'r', encoding='utf-8') as f:
            uid_mappings = json.load(f)
        slug = options['saml_provider_slug']

        for pair in uid_mappings:
            email = pair['email']
            uid = pair['student_key']
            user = User.objects.prefetch_related('social_auth').get(email=email)
            auth = user.social_auth.filter(uid__startswith=slug)[0]
            auth.uid = '{slug}:{uid}'.format(slug=slug, uid=uid)
            auth.save()
