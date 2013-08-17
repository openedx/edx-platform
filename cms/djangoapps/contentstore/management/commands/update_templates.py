from xmodule.templates import update_templates
from xmodule.modulestore.django import modulestore
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Imports and updates the Studio component templates from the code pack and put in the DB'

    def handle(self, *args, **options):
        update_templates(modulestore('direct'))
