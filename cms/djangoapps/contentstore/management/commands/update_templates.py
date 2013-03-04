from xmodule.templates import update_templates
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = \
'''Delete a MongoDB backed course'''

    def handle(self, *args, **options):
        update_templates()