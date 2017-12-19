"""
Command to delete all rows from these tables:
microsite_configuration_historicalmicrositeorganizationmapping
microsite_configuration_historicalmicrositetemplate
"""

import logging
from microsite_configuration.models import MicrositeOrganizationMapping, MicrositeTemplate
from openedx.core.djangoapps.util.row_delete import delete_rows, BaseDeletionCommand
log = logging.getLogger(__name__)


class Command(BaseDeletionCommand):
    """
    Example usage: ./manage.py lms --settings=devstack delete_historical_microsite_data
    """
    help = 'Deletes all historical MicrositeOrganizationMapping and MicrositeTemplate rows (in chunks).'

    def handle(self, *args, **options):
        """
        Deletes rows, chunking the deletes to avoid long table/row locks.
        """
        chunk_size, sleep_between = super(Command, self).handle(*args, **options)
        delete_rows(
            MicrositeOrganizationMapping.objects,
            'microsite_configuration_historicalmicrositeorganizationmapping',
            'history_id',
            chunk_size, sleep_between
        )
        delete_rows(
            MicrositeTemplate.objects,
            'microsite_configuration_historicalmicrositetemplate',
            'history_id',
            chunk_size, sleep_between
        )
