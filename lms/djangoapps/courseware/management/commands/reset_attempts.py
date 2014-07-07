#!/usr/bin/python
import csv

from request_cache.middleware import RequestCache
from xmodule.modulestore.django import modulestore
from courseware.module_tree_reset import ProctorModuleInfo

from django.conf import settings
from django.dispatch import Signal
from django.core.cache import get_cache
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError, make_option


CACHE = get_cache('mongo_metadata_inheritance')
for store_name in settings.MODULESTORE:
    store = modulestore(store_name)
    store.metadata_inheritance_cache_subsystem = CACHE
    store.request_cache = RequestCache.get_request_cache()
    modulestore_update_signal = Signal(
        providing_args=['modulestore', 'course_id', 'location'])
    store.modulestore_update_signal = modulestore_update_signal


class Command(BaseCommand):
    args = "<course_id>"
    help = """Reset exam attempts for 3.091 exam, Fall 2013. Records students \
and problems which were reset. Takes a course id and csv output filename as \
arguments."""
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dry_run',
                    action='store_true',
                    default=False,
                    help='Show what would be done without actually doing '
                    'anything'),
        make_option('--csv-output-filename',
                    dest='csv_output_filename',
                    action='store',
                    default=None,
                    help='Save stats to csv file'),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("insufficient arguments")
        course_id = args[0]
        dry_run = options['dry_run']
        csv_file = options['csv_output_filename']
        pminfo = ProctorModuleInfo(course_id)
        students = User.objects.filter(
            courseenrollment__course_id=pminfo.course.id).order_by('username')
        failed = []
        for student in students:
            failed += pminfo.get_assignments_attempted_and_failed(
                student, do_reset=not dry_run)
        if csv_file:
            self.write_to_csv(csv_file, failed)

    def write_to_csv(self, file_name, failed_assignments):
        fieldnames = ['id', 'name', 'username', 'assignment', 'problem',
                      'date', 'earned', 'possible']
        fp = open(file_name, 'w')
        csvf = csv.DictWriter(fp, fieldnames, dialect="excel", quotechar='"',
                              quoting=csv.QUOTE_ALL)
        csvf.writeheader()
        for assignment in failed_assignments:
            csvf.writerow(assignment)
        fp.close()
