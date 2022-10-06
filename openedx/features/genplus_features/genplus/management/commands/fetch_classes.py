from django.core.management.base import BaseCommand, CommandError
from openedx.features.genplus_features.genplus.rmunify import RmUnify
from openedx.features.genplus_features.genplus.constants import ClassTypes


class Command(BaseCommand):
    help = 'Fetch Classes against each school RmUnify'
    argument_options = [ClassTypes.REGISTRATION_GROUP, ClassTypes.TEACHING_GROUP]

    def add_arguments(self, parser):
        parser.add_argument("-f", type=str)

    def handle(self, *args, **options):
        if 'f' not in options or options['f'] not in self.argument_options:
            self.stdout.write(
                self.style.ERROR(f'please provide a argument -f with values {str(self.argument_options)}'))
        else:
            rm_unify = RmUnify()
            rm_unify.fetch_classes(options['f'])
            self.stdout.write(self.style.SUCCESS('Successfully fetched classes'))
