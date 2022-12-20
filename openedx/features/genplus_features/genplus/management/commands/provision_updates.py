from django.core.management.base import BaseCommand, CommandError
from openedx.features.genplus_features.genplus.rmunify import RmUnifyProvisioning


class Command(BaseCommand):
    help = 'Provision of Updates'

    def handle(self, *args, **options):
        rm_unify = RmUnifyProvisioning()
        rm_unify.provision()
        self.stdout.write(self.style.SUCCESS('DONE!!'))
