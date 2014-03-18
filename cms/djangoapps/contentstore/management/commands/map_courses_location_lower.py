"""
Script for traversing all courses and add/modify mapping with 'lower_id' and 'lower_course_id'
"""
from django.core.management.base import BaseCommand
from xmodule.modulestore.django import modulestore, loc_mapper


#
# To run from command line: ./manage.py cms --settings dev map_courses_location_lower
#
class Command(BaseCommand):
    """
    Create or modify map entry for each course in 'loc_mapper' with 'lower_id' and 'lower_course_id'
    """
    help = "Create or modify map entry for each course in 'loc_mapper' with 'lower_id' and 'lower_course_id'"

    def handle(self, *args, **options):
        # get all courses
        courses = modulestore('direct').get_courses()
        for course in courses:
            # create/modify map_entry in 'loc_mapper' with 'lower_id' and 'lower_course_id'
            loc_mapper().create_map_entry(course.location)
