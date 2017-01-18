"""
Reset persistent grades for learners.
"""
from datetime import timedelta
import logging
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from ...models import FailedTask


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Delete records of FailedTasks that have been resolved
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.

        Uses argparse syntax.  See documentation at
        https://docs.python.org/3/library/argparse.html.
        """
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help="Output what we're going to do, but don't actually do it."
        )
        parser.add_argument(
            '--task-name', '-t',
            default=None,
            help=u"Restrict cleanup to tasks matching the given task-name.",
        )
        parser.add_argument(
            '--age', '-a',
            type=int,
            default=30,
            help=u"Only delete tasks that have been resolved for at least the specified number of days",
        )

    def handle(self, *args, **options):
        tasks = FailedTask.objects.filter(datetime_resolved__lt=now() - timedelta(days=options['age']))
        if options['task_name'] is not None:
            tasks = tasks.filter(task_name=options['task_name'])
        log.info(u'Cleaning up {} tasks'.format(tasks.count()))
        if options['dry_run']:
            log.info(u"Tasks to clean up:\n{}".format(
                u'\n '.join(u'{!r}, resolved {}'.format(task, task.datetime_resolved) for task in tasks)
            ))
        else:
            tasks.delete()
