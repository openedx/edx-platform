from argparse import ArgumentTypeError
from django.core.management.base import BaseCommand, CommandError

from waffle.models import Switch


def on_off_bool(string):
    if string not in ['on', 'off']:
        raise ArgumentTypeError("invalid choice: %r (choose from 'on', "
                                "'off')" % string)
    return string == 'on'


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'name',
            nargs='?',
            help='The name of the switch.')
        parser.add_argument(
            'state',
            nargs='?',
            type=on_off_bool,
            help='The state of the switch: on or off.')
        parser.add_argument(
            '-l', '--list',
            action='store_true',
            dest='list_switches',
            default=False,
            help='List existing switches.')
        parser.add_argument(
            '--create',
            action='store_true',
            dest='create',
            default=False,
            help='If the switch does not exist, create it.')

    help = 'Activate or deactivate a switch.'

    def handle(self, *args, **options):
        if options['list_switches']:
            self.stdout.write('Switches:')
            for switch in Switch.objects.iterator():
                self.stdout.write(
                    '%s: %s' % (switch.name, 'on' if switch.active else 'off')
                )
            self.stdout.write('')
            return

        switch_name = options['name']
        state = options['state']

        if not (switch_name and state is not None):
            raise CommandError('You need to specify a switch name and state.')

        if options['create']:
            switch, created = Switch.objects.get_or_create(name=switch_name)
            if created:
                self.stdout.write('Creating switch: %s' % switch_name)
        else:
            try:
                switch = Switch.objects.get(name=switch_name)
            except Switch.DoesNotExist:
                raise CommandError('This switch does not exist.')

        switch.active = state
        switch.save()
