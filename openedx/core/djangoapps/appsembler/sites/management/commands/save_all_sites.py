from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


class Command(BaseCommand):
    help = "Force save on all sites"

    def handle(self, *args, **options):
        if not settings.ROOT_URLCONF == 'lms.urls':
            raise CommandError('This command can only be run from within the LMS')
        for sc in SiteConfiguration.objects.all():
            print('On:', sc.site.domain)
            try:
                sc.save()
                print('OK')
            except Exception as e:
                print('Error')
                print(e)
