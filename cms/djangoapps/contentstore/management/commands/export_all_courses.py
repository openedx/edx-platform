"""
Script for exporting all courseware from Mongo to a directory and listing the courses which failed to export
"""
from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.xml_exporter import export_to_xml
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore


class Command(BaseCommand):
    """
    Export all courses from mongo to the specified data directory and list the courses which failed to export
    """
    help = 'Export all courses from mongo to the specified data directory and list the courses which failed to export'

    def handle(self, *args, **options):
        """
        Execute the command
        """
        if len(args) != 1:
            raise CommandError("export requires one argument: <output path>")

        output_path = args[0]
        courses, failed_export_courses = export_courses_to_output_path(output_path)

        print("=" * 80)
        print(u"=" * 30 + u"> Export summary")
        print(u"Total number of courses to export: {0}".format(len(courses)))
        print(u"Total number of courses which failed to export: {0}".format(len(failed_export_courses)))
        print(u"List of export failed courses ids:")
        print(u"\n".join(failed_export_courses))
        print("=" * 80)


def export_courses_to_output_path(output_path):
    """
    Export all courses to target directory and return the list of courses which failed to export
    """
    content_store = contentstore()
    module_store = modulestore()
    root_dir = output_path
    courses = module_store.get_courses()

    course_ids = [x.id for x in courses]
    failed_export_courses = []

    for course_id in course_ids:
        print(u"-" * 80)
        print(u"Exporting course id = {0} to {1}".format(course_id, output_path))
        try:
            course_dir = course_id.to_deprecated_string().replace('/', '...')
            export_to_xml(module_store, content_store, course_id, root_dir, course_dir)
        except Exception as err:  # pylint: disable=broad-except
            failed_export_courses.append(unicode(course_id))
            print(u"=" * 30 + u"> Oops, failed to export {0}".format(course_id))
            print(u"Error:")
            print(err)

    return courses, failed_export_courses
