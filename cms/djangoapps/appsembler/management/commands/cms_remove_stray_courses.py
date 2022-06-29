"""
Command to remove courses without associated organization.

This command is intended as a follow-up step after `remove_site` but can be run independently.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from opaque_keys.edx.keys import CourseKey

from xmodule.contentstore.django import contentstore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore

from contentstore.utils import delete_course

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.appsembler.sites.deletion_utils import (
    confirm_deletion,
)


def get_deletable_course_keys_from_mongo():
    """
    Get keys of courses without active organization.
    """
    mongodb_course_keys = {str(mongodb_course.id) for mongodb_course in modulestore().get_course_summaries()}
    mysql_course_keys = {str(mysql_course_key) for mysql_course_key in CourseOverview.get_all_course_keys()}
    return list(mongodb_course_keys - mysql_course_keys)


def delete_course_and_assets(course_key):
    """
    Delete all courses without active organization.
    """
    course_key_obj = CourseKey.from_string(course_key)
    delete_course(course_key_obj, ModuleStoreEnum.UserID.mgmt_command, keep_instructors=False)
    contentstore().delete_all_course_assets(course_key_obj)


def cms_remove_stray_courses(commit, limit):
    """
    Remove all courses from mongodb that has no CourseOverview entry in MySQL.
    """
    course_keys = get_deletable_course_keys_from_mongo()
    if limit:
        course_keys = course_keys[:limit]

    if not course_keys:
        raise CommandError('No courses found to delete.')

    str_course_list = [str(course_key) for course_key in course_keys]
    print('Preparing to delete:')
    print('\n'.join(str_course_list))
    commit = confirm_deletion(
        question='Do you confirm to delete the courses from CMS?',
        commit=commit,
    )

    for course_key in course_keys:
        if commit:
            print('Deleting course: {}'.format(course_key))
            delete_course_and_assets(course_key)
        else:
            print('[Dry run] deleting course: {}'.format(course_key))

    print('Finished removing deletable courses')


class Command(BaseCommand):
    help = "Delete courses that don't belong to organization in `get_active_organizations()`."

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            dest='limit',
            default=1,
            type=int,
            help='Max courses to delete, use 0 to delete all courses.',
        )

        parser.add_argument(
            '--commit',
            dest='commit',
            action='store_true',
            help='Remove courses, otherwise only the log will be printed.',
        )

        parser.add_argument(
            '--dry-run',
            dest='commit',
            action='store_false',
            help='Do not remove courses, only print the logs.',
        )

    def handle(self, *args, **options):
        if settings.ROOT_URLCONF != 'cms.urls':
            raise CommandError('This command can only be run in CMS.')

        cms_remove_stray_courses(commit=options.get('commit'), limit=options['limit'])
