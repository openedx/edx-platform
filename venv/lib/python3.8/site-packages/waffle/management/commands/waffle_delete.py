from django.core.management.base import BaseCommand

from waffle import get_waffle_flag_model
from waffle.models import Sample, Switch


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--flags',
            action='store',
            dest='flag_names',
            nargs='*',
            help='List of flag names to delete.')
        parser.add_argument(
            '--samples',
            action='store',
            dest='sample_names',
            nargs='*',
            help='List of sample names to delete.')
        parser.add_argument(
            '--switches',
            action='store',
            dest='switch_names',
            nargs='*',
            help='List of switch names to delete.')

    help = 'Delete flags, samples, and switches from database'

    def handle(self, *args, **options):
        flags = options['flag_names']
        if flags:
            flag_queryset = get_waffle_flag_model().objects.filter(name__in=flags)
            flag_count = flag_queryset.count()
            flag_queryset.delete()
            self.stdout.write('Deleted %s Flags' % flag_count)

        switches = options['switch_names']
        if switches:
            switches_queryset = Switch.objects.filter(name__in=switches)
            switch_count = switches_queryset.count()
            switches_queryset.delete()
            self.stdout.write('Deleted %s Switches' % switch_count)

        samples = options['sample_names']
        if samples:
            sample_queryset = Sample.objects.filter(name__in=samples)
            sample_count = sample_queryset.count()
            sample_queryset.delete()
            self.stdout.write('Deleted %s Samples' % sample_count)
