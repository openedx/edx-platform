"""
Command to delete all rows from the api_admin_historicalapiaccessrequest table.
"""

import logging
from openedx.core.djangoapps.api_admin.models import ApiAccessRequest
from openedx.core.djangoapps.util.row_delete import delete_rows, BaseDeletionCommand
log = logging.getLogger(__name__)


class Command(BaseDeletionCommand):
    """
    Example usage: ./manage.py lms --settings=devstack delete_historical_api_admin_data
    """
    help = 'Deletes all historical ApiAccessRequest rows (in chunks).'

    def handle(self, *args, **options):
        """
        Deletes rows, chunking the deletes to avoid long table/row locks.
        """
        chunk_size, sleep_between = super(Command, self).handle(*args, **options)
        delete_rows(
            ApiAccessRequest.objects,
            'api_admin_historicalapiaccessrequest',
            'history_id',
            chunk_size, sleep_between
        )
