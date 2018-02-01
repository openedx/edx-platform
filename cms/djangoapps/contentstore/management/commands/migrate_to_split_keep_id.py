"""
Django management command to migrate a course from the old Mongo modulestore
to the new split-Mongo modulestore.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from contentstore.management.commands.utils import user_from_str
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.split_migrator import SplitMigrator

from student.roles import CourseInstructorRole


class Command(BaseCommand):
    """
    Migrate a course from old-Mongo to split-Mongo. It reuses the old course id except where overridden.
    """

    help = "Migrate a course from old-Mongo to split-Mongo, but keep the existing Course Key."

    def add_arguments(self, parser):
        parser.add_argument('course_key')

    def handle(self, *args, **options):
        course_key = CourseKey.from_string(options['course_key'])
        instructor_role = CourseInstructorRole(course_key=course_key)
        instructor = instructor_role.users_with_role()[0]

        migrator = SplitMigrator(
            split_modulestore=modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.split),
            source_modulestore=modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.mongo),
        )

        migrator.migrate_with_same_course_key(course_key, instructor.id)
