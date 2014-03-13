"""
Script for exporting courseware from Mongo to a tar.gz file
"""
import os

from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.xml_exporter import export_to_xml
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.keys import CourseKey
from xmodule.contentstore.django import contentstore
from xmodule.course_module import CourseDescriptor


class Command(BaseCommand):
    """
    Export the specified data directory into the default ModuleStore
    """
    help = 'Export the specified data directory into the default ModuleStore'

    def handle(self, *args, **options):
        "Execute the command"
        if len(args) != 2:
            raise CommandError("export requires two arguments: <course id> <output path>")

        course_id = CourseKey.from_string(args[0])
        output_path = args[1]

        print("Exporting course id = {0} to {1}".format(course_id, output_path))

        root_dir = os.path.dirname(output_path)
        course_dir = os.path.splitext(os.path.basename(output_path))[0]

        export_to_xml(modulestore('direct'), contentstore(), course_id, root_dir, course_dir, modulestore())
