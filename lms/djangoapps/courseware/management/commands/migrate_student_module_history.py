# pylint: disable=missing-docstring

from datetime import timedelta
from textwrap import dedent
import time
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import transaction

from courseware.models import StudentModuleHistory, StudentModuleHistoryArchive

SQL_MAX_INT = 2**31 - 1

class Command(BaseCommand):
    """
    Command to migrate data from StudentModuleHistoryArchive into StudentModuleHistory.
    Works from largest ID to smallest.
    """
    help = dedent(__doc__).strip()
    option_list = BaseCommand.option_list + (
        make_option('-i', '--index', type='int', default=0, dest='index',
            help='chunk index to sync (0-indexed)'),
        make_option('-n', '--num-chunks', type='int', default=1, dest='num_chunks',
            help='number of chunks to use'),
        make_option('-w', '--window', type='int', default=1000, dest='window',
            help='how many rows to migrate per query'),
    )

    def handle(self, *arguments, **options):
        opts, args = _parse_args(arguments, options)
        if options['index'] >= options['num_chunks']:
            self.stdout.write("Index {} is too large for {} chunks".format(options['index'], options['num_chunks']))
            return

        try:
            StudentModuleHistory.objects.all().order_by('id')[0]
        except IndexError:
            self.stdout.write("No entries found in StudentModuleHistory, aborting migration.\n")
            return

        chunk_size = SQL_MAX_INT / options['num_chunks']

        min_id = chunk_size * options['index']

        if options['index'] == options['num_chunks'] - 1:
            max_id = SQL_MAX_INT
        else:
            max_id = chunk_size * options['index'] + chunk_size - 1

        self.migrate_range(min_id, max_id, options['window'])


    @transaction.commit_manually
    def _migrate_range(self, min_id, max_id, window):
        self.stdout.write("Migrating StudentModuleHistoryArchive entries {}-{}\n".format(max_id, min_id))
        start_time = time.time()

        archive_entries = (
            StudentModuleHistoryArchive.objects
            .select_related('student_module__student')
            .order_by('-id')
        )

        real_max_id = None
        count = 0
        current_max_id = max_id

        try:
            while current_max_id > min_id:
                entries = archive_entries.filter(id__lt=current_max_id, id__gte=max(current_max_id - window, min_id))

                new_entries = [StudentModuleHistory.from_archive(entry) for entry in entries]

                StudentModuleHistory.objects.bulk_create(new_entries)
                count += len(new_entries)

                if new_entries:
                    if real_max_id is None:
                        real_max_id = new_entries[0].id

                    transaction.commit()
                    duration = time.time() - start_time

                    self.stdout.write("Migrated StudentModuleHistoryArchive {}-{} to StudentModuleHistory\n".format(new_entries[0].id, new_entries[-1].id))
                    self.stdout.write("Migrating {} entries per second. {} seconds remaining...\n".format(
                        count / duration,
                        timedelta(seconds=(new_entries[-1].id - min_id) / count * duration),
                    ))

                current_max_id -= window
        except:
            transaction.rollback()
            raise
        else:
            transaction.commit()

            if new_entries:
                self.stdout.write("Migrated StudentModuleHistoryArchive {}-{} to StudentModuleHistory\n".format(real_max_id, new_entries[-1].id))
                self.stdout.write("Migration complete\n")
            else:
                self.stdout.write("No migration needed\n")
