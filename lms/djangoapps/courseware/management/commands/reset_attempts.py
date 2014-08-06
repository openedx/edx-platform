#!/usr/bin/python
import csv

from courseware.module_tree_reset import ProctorModuleInfo

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError, make_option


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
        make_option('--wipe-randomize-history',
                    dest='wipe_history',
                    action='store_true',
                    default=False,
                    help="Reset randomization xmodule's history tracking"),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("insufficient arguments")
        course_id = args[0]
        dry_run = options['dry_run']
        csv_file = options['csv_output_filename']
        wipe_history = options['wipe_history']
        pminfo = ProctorModuleInfo(course_id)
        students = User.objects.filter(
            courseenrollment__course_id=pminfo.course.id).order_by('username')
        failed = []
        for student in students:
            failed += pminfo.get_assignments_attempted_and_failed(
                student, reset=not dry_run,
                wipe_randomize_history=wipe_history)
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
