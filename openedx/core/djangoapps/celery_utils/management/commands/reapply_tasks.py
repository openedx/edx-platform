"""
Reset persistent grades for learners.
"""
import logging
from textwrap import dedent

from django.core.management.base import BaseCommand

from ...models import FailedTask

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Reapply tasks that failed previously.
    """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.

        Uses argparse syntax.  See documentation at
        https://docs.python.org/3/library/argparse.html.
        """
        parser.add_argument(
            '--task-name', '-t',
            action='store',
            default=None,
            help=u"Restrict reapplied tasks to those matching the given task-name."
        )

    def handle(self, *args, **options):
        tasks = FailedTask.objects.filter(datetime_resolved=None)
        if options['task_name'] is not None:
            tasks = tasks.filter(task_name=options['task_name'])
        log.info(u'Reapplying {} tasks'.format(tasks.count()))
        log.debug(u'Reapplied tasks: {}'.format(list(tasks)))
        seen_tasks = set()
        for task in tasks:
            if task.task_id in seen_tasks:
                continue
            seen_tasks.add(task.task_id)
            task.reapply()
