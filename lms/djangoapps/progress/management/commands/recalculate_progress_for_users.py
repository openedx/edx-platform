"""
One-time data migration script -- should not need to run it again
"""
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q

from progress.models import StudentProgress, CourseModuleCompletion
from progress.signals import is_valid_progress_module
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Recalculate progress entries for the specified course(s) and/or user(s)
    """
    help = 'Recalculate existing users progress per course'
    option_list = BaseCommand.option_list + (
        make_option(
            "-c",
            "--course_ids",
            dest="course_ids",
            help="List of courses for which to Recalculate progress",
            metavar="first/course/id,second/course/id"
        ),
        make_option(
            "-u",
            "--user_ids",
            dest="user_ids",
            help="List of users for which to Recalculate progress",
            metavar="1234,2468,3579"
        ),
    )

    def handle(self, *args, **options):
        course_ids = options.get('course_ids')
        user_ids = options.get('user_ids')

        status_summary = {'skipped': 0, 'updated': 0}
        total_users_processed = 0
        detached_categories = getattr(settings, 'PROGRESS_DETACHED_CATEGORIES', [])
        cat_list = [Q(content_id__contains=item.strip()) for item in detached_categories]
        cat_list = reduce(lambda a, b: a | b, cat_list)

        # Get the list of courses from the system
        courses = modulestore().get_courses()

        # If one or more courses were specified by the caller, just use those ones...
        if course_ids is not None:
            filtered_courses = []
            for course in courses:
                if unicode(course.id) in course_ids.split(','):
                    filtered_courses.append(course)
            courses = filtered_courses

        for course in courses:
            users = CourseEnrollment.objects.users_enrolled_in(course.id)
            # If one or more users were specified by the caller, just use those ones...
            if user_ids is not None:
                filtered_users = []
                for user in users:
                    if str(user.id) in user_ids.split(','):
                        filtered_users.append(user)
                users = filtered_users

            # For each user...
            for user in users:
                total_users_processed += 1
                status = 'skipped'
                completions = CourseModuleCompletion.objects.filter(course_id=course.id, user_id=user.id)\
                    .exclude(cat_list).values_list('content_id', flat=True).distinct()

                num_completions = sum([is_valid_progress_module(content_id=content_id) for content_id in completions])
                try:
                    existing_record = StudentProgress.objects.get(user=user, course_id=course.id)

                    if existing_record.completions != num_completions:
                        existing_record.completions = num_completions
                        status = 'updated'

                    if status == 'updated':
                        existing_record.save()

                except StudentProgress.DoesNotExist:
                    status = "skipped"

                log_msg = 'Progress entry {} -- Course: {}, User: {}  (completions: {})'.format(
                    status,
                    course.id,
                    user.id,
                    num_completions
                )

                status_summary[status] += 1
                log.info(log_msg)
        print "command completed. Total users processed", total_users_processed, status_summary
