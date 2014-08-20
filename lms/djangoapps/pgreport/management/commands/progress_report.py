"""
   Django management command to create or get or delete report of progress
"""
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from pgreport.views import get_pgreport_csv, delete_pgreport_csv
from pgreport.tasks import check_course_id
from xmodule.exceptions import NotFoundError
from django.core.management import call_command


class Command(BaseCommand):
    args = "<course_id>"
    help = """  progress_report: Get progress report.\n  progress_report -c: Create progress report.\n  progress_report -d: Delete progress report."""
    option_list = BaseCommand.option_list + (
        make_option(
            '-c', '--create-report',
            action="store_true",
            default=False,
            dest='create',
            help='Create the progress of students.'
        ),
        make_option(
            '-d', '--delete-report',
            action="store_true",
            default=False,
            dest='delete',
            help='Delete the progress of students.'
        ),
    )

    def handle(self, *args, **options):
        create_report = options['create']
        delete_report = options['delete']

        if len(args) != 1:
            raise CommandError('"course_id" is not specified')
        elif create_report and delete_report:
            raise CommandError(
                'Cannot specify "-c" option and "-d" option at the same time.')

        course_id = args[0]
        check_course_id(course_id)

        if delete_report:
            delete_pgreport_csv(course_id)
        elif create_report:
            call_command('create_report_task', *['create'], **{'course_id': course_id})
        else:
            try: 
                get_pgreport_csv(course_id)
            except NotFoundError:
                raise CommandError("CSV not found.")
