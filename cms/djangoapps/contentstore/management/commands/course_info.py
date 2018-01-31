"""
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
    Get course information from different modulestores
    """

    help = "Migrate a course from old-Mongo to split-Mongo, but keep the existing Course Key."

    def add_arguments(self, parser):
        parser.add_argument('course_key')

    def handle(self, *args, **options):
        course_key = CourseKey.from_string(options['course_key'])

        split_modulestore=modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.split)
        source_modulestore=modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.mongo)

        print "From Old Mongo"
        print "--------------"
        print source_modulestore.get_course(course_key)
        print "\n"
        print "From Split"
        print "----------"
        print split_modulestore.get_course(course_key)
