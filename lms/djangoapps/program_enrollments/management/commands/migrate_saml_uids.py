"""
Management command to re-write UIDs identifying learners in external organizations' systems

Intented for use in production environments, to help support migration
of existing SSO learners into our most-recent program enrollment flow
without needing to manually re-link their account.
"""
from __future__ import absolute_import, unicode_literals

import logging
from textwrap import dedent

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Updates UserSocialAuth records to use UIDs provided in the supplied JSON file

    Example usage:
        $ ./manage.py lms migrate_saml_uids.py \
          --uid-mapping=change@my.uid:4045A285AF596D8589C24841657CA3D8,me@too.uid:4045A285AF596D8589C24841657CA3D9 \
          --saml-provider-slug=default
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        parser.add_argument(
            '--uid-mapping',
            help='comma-separated list of email:uid mappings'
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
        pairs = options['uid_mapping'].split(',')
        slug = options['saml_provider_slug']

        for pair in pairs:
            uid_list = pair.split(':')
            email = uid_list[0]
            uid = uid_list[1]
            user = User.objects.prefetch_related('social_auth').get(email=email)
            auth = user.social_auth.filter(uid__startswith=slug)[0]
            auth.uid = '{slug}:{uid}'.format(slug=slug, uid=uid)
            auth.save()
