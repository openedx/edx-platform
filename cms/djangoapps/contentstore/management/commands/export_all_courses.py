"""
Script for exporting all courseware from Mongo to a directory
"""
from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.xml_exporter import export_to_xml
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore


class Command(BaseCommand):
    """Export all courses from mongo to the specified data directory"""
    help = 'Export all courses from mongo to the specified data directory'

    def handle(self, *args, **options):
        "Execute the command"
        if len(args) != 1:
            raise CommandError("export requires one argument: <output path>")

        output_path = args[0]

        cs = contentstore()
        ms = modulestore()
        root_dir = output_path
        courses = ms.get_courses()

        print("%d courses to export:" % len(courses))
        cids = [x.id for x in courses]
        print(cids)

        for course_id in cids:

            print("-"*77)
            print("Exporting course id = {0} to {1}".format(course_id, output_path))

            if 1:
                try:
                    course_dir = course_id.replace('/', '...')
                    export_to_xml(ms, cs, course_id, root_dir, course_dir)
                except Exception as err:
                    print("="*30 + "> Oops, failed to export %s" % course_id)
                    print("Error:")
                    print(err)
