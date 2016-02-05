from django.db.backends.signals import connection_created
import logging

log = logging.getLogger(__name__)

def configure_connection(sender, connection, **kwargs):
    """Make sqlite go way faster."""
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA temp_store = MEMORY')
        cursor.execute('PRAGMA synchronous = OFF')
        cursor.execute('PRAGMA cache_size = 16384')
        cursor.execute('PRAGMA fullfsync = OFF')
        cursor.execute('PRAGMA checkpoint_fullfsync = OFF')

        log.info('Altered SQLite connection for test mode.')

connection_created.connect(configure_connection)