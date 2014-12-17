"""
   Django management command to create progress report.
"""
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator
from pgreport.tasks import create_report_task, ProgressReportTask, TaskState
from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    args = "<create or list or status or revoke>"
    help = """Push task that create progress_modules report\n  create_report_task create: Create progress report.\n  create_report_task list: List active tasks.\n  create_report_task status -t [task_id]: Show task status.\n  create_report_task revoke -t [task_id]: Revoke task.\n create_report_task clear_cache -c [course_id]: clear memcache."""
    option_list = BaseCommand.option_list + (
        make_option(
            '-c', '--course-id',
            action="store",
            default=None,
            dest='course_id',
            help='course_id that create progress report.'
        ),
        make_option(
            '-t', '--task-id',
            action="store",
            default=None,
            dest='task_id',
            help='task_id that show status or revoke task'
        ),
    )

    def handle(self, *args, **options):
        """Handle command options."""
        course_id = options['course_id']
        task_id = options['task_id']

        if course_id is not None:
            try:
                course_id = CourseLocator.from_string(course_id)
            except InvalidKeyError:
                raise CommandError("'{}' is an invalid course_id".format(course_id))
            if not modulestore().get_course(course_id):
                raise CommandError("The specified course does not exist.")

        if len(args) != 1:
            raise CommandError(
                'Required subcommand, create, list, status, revoke or clear_cache.')
        command = args[0]
        task = ProgressReportTask(create_report_task)

        if command == "status":
            if task_id is None:
                raise CommandError('"status" subcommand required task_id.')
            task.show_task_status(task_id)
        elif command == "list":
            task.show_task_list()
        elif command == "revoke":
            if task_id is None:
                raise CommandError('"revoke" subcommand required task_id.')
            task.revoke_task(task_id)
        elif command == "create":
            if course_id is None:
                raise CommandError('"create" subcommand required course_id.')
            task.send_task(course_id)
        elif command == "clear_cache":
            if course_id is None:
                raise CommandError('"clear_cache" subcommand required course_id.')
            state = TaskState("pgreport.tasks.create_report_task", course_id)
            state.delete_task_state()
        else:
            raise CommandError('Invalid subcommand.')
