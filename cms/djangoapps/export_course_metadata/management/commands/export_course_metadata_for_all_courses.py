"""
Export course metadata for all courses
"""

from django.core.management.base import BaseCommand

from xmodule.modulestore.django import modulestore

from cms.djangoapps.export_course_metadata.signals import export_course_metadata


class Command(BaseCommand):
    """
    Export course metadata for all courses
    """
    help = 'Export course metadata for all courses'

    def handle(self, *args, **options):
        """
        Execute the command
        """
        export_course_metadata_for_all_courses()


def export_course_metadata_for_all_courses():
    """
    Export course metadata for all courses
    """
    module_store = modulestore()
    courses = module_store.get_courses()

    for course in courses:
        export_course_metadata(None, course.id)
