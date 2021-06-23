"""
management command to link existing user & courses with arbisoft & edly organization.
"""
# todo: remove this command once it's executed on all envs
from logging import getLogger

from django.core.management.base import BaseCommand
from organizations.models import Organization

from student.models import UserProfile

log = getLogger(__name__)


class Command(BaseCommand):
    """
    A management command that will link existing user & courses with arbisoft & edly organization.
    """

    help = 'Link existing user & courses with arbisoft & edly organization'

    def handle(self, *args, **options):
        log.info('Staring command to link existing user & courses with arbisoft & edly organization')

        arbisoft_org, _ = Organization.objects.get_or_create(name='arbisoft', short_name='arbisoft')
        edly_org, _ = Organization.objects.get_or_create(name='edly', short_name='edly')

        UserProfile.objects.filter(user__email__endswith='@arbisoft.com').update(organization=arbisoft_org)
        UserProfile.objects.filter(user__email__endswith='@edly.io').update(organization=edly_org)
