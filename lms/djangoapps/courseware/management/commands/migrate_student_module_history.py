# pylint: disable=missing-docstring

from datetime import timedelta
from textwrap import dedent
import time

from django.core.management.base import BaseCommand
from django.db import transaction

from courseware.models import StudentModuleHistory, StudentModuleHistoryArchive


class Command(BaseCommand):
    """
    Command to migrate all data from StudentModuleHistoryArchive into StudentModuleHistory.
    """
    help = dedent(__doc__).strip()

    @transaction.commit_manually
    def handle(self, *args, **options):
        try:
            max_id = StudentModuleHistory.objects.all().order_by('id')[0].id
        except IndexError:
            self.stdout.write("No entries found in StudentModuleHistory, aborting migration.\n")
            return

        start_time = time.time()

        self.stdout.write("Migrating StudentModuleHistoryArchive entries before {}\n".format(max_id))
        archive_entries = (
            StudentModuleHistoryArchive.objects
            .select_related('student')
            .filter(id__lt=max_id)
            .order_by('-id')
        )

        entry = None

        for count, entry in enumerate(archive_entries):
            StudentModuleHistory.from_archive(entry).save()
            if count % 1000 == 0:
                transaction.commit()
                duration = time.time() - start_time
                self.stdout.write("Migrated StudentModuleHistoryArchive {} to StudentModuleHistory\n".format(entry.id))
                self.stdout.write("Migrating {} entries per second. {} seconds remaining...\n".format(
                    (count + 1) / duration,
                    timedelta(seconds=(entry.id / (count + 1)) * duration),
                ))

        transaction.commit()
        if entry:
            self.stdout.write("Migrated StudentModuleHistoryArchive {} to StudentModuleHistory\n".format(entry.id))
            self.stdout.write("Migration complete\n")
        else:
            self.stdout.write("No migration needed\n")
