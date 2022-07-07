from __future__ import print_function

from django.core.management.base import BaseCommand
from django_crontab.crontab import Crontab


class Command(BaseCommand):
    help = 'run this command to add, show or remove the jobs defined in CRONJOBS setting from/to crontab'

    def add_arguments(self, parser):
        parser.add_argument('subcommand', choices=['add', 'show', 'remove', 'run'])
        parser.add_argument('jobhash', nargs='?')

    def handle(self, *args, **options):
        """
        Dispatches by given subcommand
        """
        if options['subcommand'] == 'add':
            with Crontab(**options) as crontab:
                crontab.remove_jobs()
                crontab.add_jobs()
        elif options['subcommand'] == 'show':
            with Crontab(readonly=True, **options) as crontab:
                crontab.show_jobs()
        elif options['subcommand'] == 'remove':
            with Crontab(**options) as crontab:
                crontab.remove_jobs()
        elif options['subcommand'] == 'run':
            Crontab().run_job(options['jobhash'])
        else:
            print(self.help)
