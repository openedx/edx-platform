"""
A Command which, given a mapping of V1 to V2 Libraries,
edits all xblocks in courses which refer to the v1 library to point to the v2 library.
"""

import logging
import csv

from django.core.management import BaseCommand, CommandError
from celery import group
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from cms.djangoapps.contentstore.tasks import replace_all_library_source_blocks_ids_for_course

log = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py cms replace_v1_lib_refs_with_v2_in_courses '/path/to/file/containing/library_mappings.csv'
        $ ./manage.py cms replace_v1_lib_refs_with_v2_in_courses '/path/to/file/containing/library_mappings.csv'

    """
    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV file.')

    def replace_all_library_source_blocks_ids(self, v1_to_v2_lib_map):
        """A method to replace 'source_library_id' in all relevant blocks."""

        courses =  CourseOverview.get_all_courses()
        # Use Celery to distribute the workload

        tasks = group(replace_all_library_source_blocks_ids_for_course.s(course, v1_to_v2_lib_map) for course in courses)
        results = tasks.apply_async()

        for result in results.get():
            if isinstance(result, Exception):
                # Handle the task failure here
                log.error("Task failed with error: %s", str(result))
                continue
        log.info("Completed replacing all v1 library source ids with v2 library source ids")

    def handle(self, *args, **kwargs):
        """ Parse Arguements and begin Command"""
        file_path = kwargs['file_path']
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:

                if not file_path.endswith('.csv'):
                    raise CommandError('Invalid file format. Only CSV files are supported.')

                csv_reader = csv.reader(csvfile)
                v1_to_v2_lib_map = {}

                for row in csv_reader:
                    if len(row) >= 2:
                        print(row)
                        key = row[0].strip()
                        value = row[1].strip()
                        v1_to_v2_lib_map[key] = value

                print("Data successfully imported as dictionary:")
                print(v1_to_v2_lib_map)

        except FileNotFoundError:
            log.error("File not found at '%s'.", {file_path})
        except Exception as e:
            log.error("An error occurred: %s", {str(e)})

        print("Cherry")
        print(v1_to_v2_lib_map)

        self.replace_all_library_source_blocks_ids(v1_to_v2_lib_map)