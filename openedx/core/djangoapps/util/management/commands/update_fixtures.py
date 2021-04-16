"""
Django management command to update the loaded test fixtures as necessary for
the current test environment.  Currently just sets an appropriate domain for
each Site fixture.
"""


import os

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    update_fixtures management command
    """

    help = "Update fixtures to match the current test environment."

    def handle(self, *args, **options):
        if 'BOK_CHOY_HOSTNAME' in os.environ:
            # Fix the Site fixture domains so third party auth tests work correctly
            host = os.environ['BOK_CHOY_HOSTNAME']
            cms_port = os.environ['BOK_CHOY_CMS_PORT']
            lms_port = os.environ['BOK_CHOY_LMS_PORT']
            cms_domain = f'{host}:{cms_port}'
            Site.objects.filter(name='cms').update(domain=cms_domain)
            lms_domain = f'{host}:{lms_port}'
            Site.objects.filter(name='lms').update(domain=lms_domain)
