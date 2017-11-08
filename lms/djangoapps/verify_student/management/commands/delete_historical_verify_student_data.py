"""
Command to delete all rows from the verify_student_historicalverificationdeadline table.
"""

import logging
from lms.djangoapps.verify_student.models import VerificationDeadline
from openedx.core.djangoapps.util.row_delete import delete_rows, BaseDeletionCommand
log = logging.getLogger(__name__)


class Command(BaseDeletionCommand):
    """
    Example usage: ./manage.py lms --settings=devstack delete_historical_verify_student_data
    """
    help = 'Deletes all historical VerificationDeadline rows (in chunks).'

    def handle(self, *args, **options):
        """
        Deletes rows, chunking the deletes to avoid long table/row locks.
        """
        chunk_size, sleep_between = super(Command, self).handle(*args, **options)
        delete_rows(
            VerificationDeadline.objects,
            'verify_student_historicalverificationdeadline',
            'history_id',
            chunk_size, sleep_between
        )
