"""
Command to delete all rows from the student_historicalcourseenrollment table.
"""

from __future__ import absolute_import

import logging

from openedx.core.djangoapps.util.row_delete import BaseDeletionCommand, delete_rows
from student.models import CourseEnrollment

log = logging.getLogger(__name__)


class Command(BaseDeletionCommand):
    """
    Example usage: ./manage.py lms --settings=devstack delete_historical_enrollment_data
    """
    help = 'Deletes all historical CourseEnrollment rows (in chunks).'

    def handle(self, *args, **options):
        """
        Deletes rows, chunking the deletes to avoid long table/row locks.
        """
        chunk_size, sleep_between = super(Command, self).handle(*args, **options)
        delete_rows(
            CourseEnrollment.objects,
            'student_historicalcourseenrollment',
            'history_id',
            chunk_size, sleep_between
        )
