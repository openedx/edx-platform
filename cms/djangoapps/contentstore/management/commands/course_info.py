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
from pprint import PrettyPrinter

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

        pp = PrettyPrinter()

        print "From Old Mongo"
        print "--------------"
        old_mongo_course = source_modulestore.get_course(course_key)
        if old_mongo_course is not None:
            old_mongo_fields = {
                field_name: field.read_from(old_mongo_course)
                for field_name, field in old_mongo_course.fields.items()
                if field.is_set_on(old_mongo_course)
            }
            print pp.pprint(old_mongo_fields)
        print "\n"
        print "From Split"
        print "----------"
        split_course = split_modulestore.get_course(course_key)
        if split_course is not None:
            split_fields = {
                field_name: field.read_from(split_course)
                for field_name, field in split_course.fields.items()
                if field.is_set_on(split_course)
            }
            print pp.pprint(split_fields)
