"""
Script for exporting courseware from Mongo to a tar.gz file
"""
import os

from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.xml_exporter import export_course_to_xml
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey
from xmodule.contentstore.django import contentstore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class Command(BaseCommand):
    """
    Export the specified data directory into the default ModuleStore
    """
    help = 'Export the specified data directory into the default ModuleStore'

    def add_arguments(self, parser):
        parser.add_argument('course_id')
        parser.add_argument('output_path')

    def handle(self, *args, **options):
        """Execute the command"""
        try:
            course_key = CourseKey.from_string(options['course_id'])
        except InvalidKeyError:
            try:
                course_key = SlashSeparatedCourseKey.from_deprecated_string(options['course_id'])
            except InvalidKeyError:
                raise CommandError("Invalid course_key: '%s'." % options['course_id'])

        if not modulestore().get_course(course_key):
            raise CommandError("Course with %s key not found." % options['course_id'])

        output_path = options['output_path']

        print "Exporting course id = {0} to {1}".format(course_key, output_path)

        if not output_path.endswith('/'):
            output_path += '/'

        root_dir = os.path.dirname(output_path)
        course_dir = os.path.splitext(os.path.basename(output_path))[0]

        export_course_to_xml(modulestore(), contentstore(), course_key, root_dir, course_dir)
