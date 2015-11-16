# pylint: disable=missing-docstring

from datetime import timedelta
from textwrap import dedent
import time
from optparse import make_option
from sys import exit

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
            help='chunk index to sync (0-indexed) [default: %default]'),
        make_option('-n', '--num-chunks', type='int', default=1, dest='num_chunks',
            help='number of chunks to use [default: %default]'),
        make_option('-w', '--window', type='int', default=1000, dest='window',
            help='how many rows to migrate per query [default: %default]'),
        make_option('-s', '--show-range', action='store_true', default=False, dest='show_range',
            help="show the range that this command would've run over and the max id in that range")
    )

    def handle(self, *arguments, **options):
        if options['index'] >= options['num_chunks']:
            self.stdout.write("Index {} is too large for {} chunks\n".format(options['index'], options['num_chunks']))
            exit(2)

        #Set max and min id from the number of chunks and the selected index
        chunk_size = SQL_MAX_INT / options['num_chunks']
        min_id = chunk_size * options['index']

        if options['index'] == options['num_chunks'] - 1:
            max_id = SQL_MAX_INT
        else:
            max_id = chunk_size * options['index'] + chunk_size - 1

        #Start at the max id in the selected range, so the migration is resumable
        active_range = StudentModuleHistory.objects.filter(id__lt=max_id, id__gte=min_id).order_by('id')
        if active_range:
            min_id_already_migrated = active_range[0].id
            self.stdout.write("Found min existent id {} in StudentModuleHistory, resuming from there\n".format(min_id_already_migrated))
        else:
            #Assume we're starting from the top of the range
            min_id_already_migrated = max_id
            self.stdout.write("No entries found in StudentModuleHistory in this range, starting at top of range ({})\n".format(min_id_already_migrated))

        #Make sure there's entries to migrate in StudentModuleHistoryArchive in this range
        try:
            StudentModuleHistoryArchive.objects.filter(id__lt=min_id_already_migrated, id__gte=min_id)[0]
        except:
            self.stdout.write("No entries found in StudentModuleHistoryArchive in range {}-{}, aborting migration.\n".format(
                min_id_already_migrated, min_id))
            return

        if options['show_range']:
            self.stdout.write("Range: {}-{}, min id in range: {}\n".format(max_id, min_id, min_id_already_migrated))
            return

        self._migrate_range(min_id, min_id_already_migrated, options['window'])


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
