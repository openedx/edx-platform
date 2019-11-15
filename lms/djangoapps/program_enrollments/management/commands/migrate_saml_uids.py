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

        email_map = { m['email']: {'uid': m['student_key'], 'updated': False, 'counted': False } for m in uid_mappings }
        user_queryset = User.objects.prefetch_related('social_auth').filter(social_auth__uid__startswith=slug + ':')
        users = [u for u in user_queryset]

        missed = 0
        updated = 0
        for user in users:
            email = user.email
            try:
                info_for_email = email_map[email]
            except KeyError:
                missed += 1
                continue
            info_for_email['updated'] = True
            uid = info_for_email['uid']
            auth = user.social_auth.filter(uid__startswith=slug + ':')[0]
            # print something about the ones who have more than one social_auth from gatech
            auth.uid = '{slug}:{uid}'.format(slug=slug, uid=uid)
            auth.save()
            updated += 1

        not_previously_linked = 0
        updated = 0
        duplicated_in_mapping = 0
        for mapping in uid_mappings:
            info_for_email = email_map[mapping['email']]
            if not info_for_email['counted']:
                not_previously_linked += not info_for_email['updated']
                updated += info_for_email['updated']
                info_for_email['counted'] = True
            else:
                duplicated_in_mapping += 1

        log.info(
            'Number of users with {slug} UserSocialAuth records for which there was no mapping in the provided file: {missed}'.format(
                slug=slug,
                missed=missed
        ))
        log.info(
            'Number of users identified in the mapping file without {slug} UserSocialAuth records: {not_previously_linked}'.format(
                slug=slug,
                not_previously_linked=not_previously_linked
        ))
        log.info('Number of mappings in the mapping file where the identified user has already been processed: {duplicated_in_mapping}'.format(
            duplicated_in_mapping=duplicated_in_mapping
        ))


