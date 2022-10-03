from django.core.management.base import BaseCommand, CommandError
from openedx.features.genplus_features.genplus.rmunify import RmUnify


class Command(BaseCommand):
    help = 'Fetch Schools from RmUnify'

    def handle(self, *args, **options):
        rm_unify = RmUnify()
        rm_unify.fetch_schools()
        self.stdout.write(self.style.SUCCESS('DONE!!'))
