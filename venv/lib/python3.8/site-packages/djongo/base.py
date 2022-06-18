"""
MongoDB database backend for Django
"""
from collections import OrderedDict
from logging import getLogger
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.client import BaseDatabaseClient
from logging.config import dictConfig
from django.db.utils import Error
from .creation import DatabaseCreation
from . import database as Database
from .cursor import Cursor
from .features import DatabaseFeatures
from .introspection import DatabaseIntrospection
from .operations import DatabaseOperations
from .schema import DatabaseSchemaEditor

logger = getLogger(__name__)


class CachedCollections(set):

    def __init__(self, database):
        self.db = database
        super().__init__()

    def __contains__(self, item):
        ans = super().__contains__(item)
        if ans:
            return ans
        self.update(self.db.list_collection_names())
        return super().__contains__(item)


class DjongoClient:

    def __init__(self, database, enforce_schema=True):
        self.enforce_schema = enforce_schema
        self.cached_collections = CachedCollections(database)


class DatabaseWrapper(BaseDatabaseWrapper):
    """
    DatabaseWrapper for MongoDB using SQL replacements.
    """

    # This dictionary will map Django model field types to appropriate data
    # types to be used in the database.
    data_types = {
        'AutoField': 'int',
        'BigAutoField': 'long',
        'BinaryField': 'binData',
        'BooleanField': 'bool',
        'CharField': 'string',
        'CommaSeparatedIntegerField': 'string',
        'DateField': 'date',
        'DateTimeField': 'date',
        'DecimalField': 'decimal',
        'DurationField': 'long',
        'FileField': 'string',
        'FilePathField': 'string',
        'FloatField': 'double',
        'IntegerField': 'int',
        'BigIntegerField': 'long',
        'IPAddressField': 'string',
        'GenericIPAddressField': 'string',
        'NullBooleanField': 'bool',
        'OneToOneField': 'int',
        'PositiveIntegerField': 'long',
        'PositiveSmallIntegerField': 'int',
        'SlugField': 'string',
        'SmallIntegerField': 'int',
        'TextField': 'string',
        'TimeField': 'date',
        'UUIDField': 'string',
        'GenericObjectIdField': 'objectId',
        'ObjectIdField': 'objectId',
        'EmbeddedField': 'object',
        'ArrayField': 'array'
    }

    data_types_suffix = {
        'AutoField': 'AUTOINCREMENT',
        'BigAutoField': 'AUTOINCREMENT',
        'ObjectIdField': 'AUTOINCREMENT'
    }

    operators = {
        'exact': '= %s',
        'iexact': 'iLIKE %s',
        'contains': 'LIKE %s',
        'icontains': 'iLIKE %s',
        'regex': 'REGEXP BINARY %s',
        'iregex': 'REGEXP %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': 'LIKE %s',
        'endswith': 'LIKE %s',
        'istartswith': 'iLIKE %s',
        'iendswith': 'iLIKE %s',
    }

    vendor = 'djongo'
    SchemaEditorClass = DatabaseSchemaEditor
    Database = Database

    client_class = BaseDatabaseClient
    creation_class = DatabaseCreation
    features_class = DatabaseFeatures
    introspection_class = DatabaseIntrospection
    ops_class = DatabaseOperations

    def __init__(self, *args, **kwargs):
        self.client_connection = None
        self.djongo_connection = None
        super().__init__(*args, **kwargs)

    def is_usable(self):
        if self.connection is not None:
            return True
        return False

    def get_connection_params(self):
        """
        Default method to acquire database connection parameters.

        Sets connection parameters to match settings.py, and sets
        default values to blank fields.
        """
        valid_settings = {
            'NAME': 'name',
            'ENFORCE_SCHEMA': 'enforce_schema',
        }
        connection_params = {
            'name': 'djongo_test',
            'enforce_schema': False
        }
        for setting_name, kwarg in valid_settings.items():
            try:
                setting = self.settings_dict[setting_name]
            except KeyError:
                continue

            if setting or setting is False:
                connection_params[kwarg] = setting
        try:
            connection_params.update(self.settings_dict['CLIENT'])
        except KeyError:
            pass

        return connection_params

    def get_new_connection(self, connection_params):
        """
        Receives a dictionary connection_params to setup
        a connection to the database.

        Dictionary correct setup is made through the
        get_connection_params method.
        """

        name = connection_params.pop('name')
        es = connection_params.pop('enforce_schema')

        connection_params['document_class'] = OrderedDict
        # connection_params['tz_aware'] = True
        # To prevent leaving unclosed connections behind,
        # client_conn must be closed before a new connection
        # is created.
        if self.client_connection is not None:
            self.client_connection.close()
            logger.debug('Existing MongoClient connection closed')

        self.client_connection = Database.connect(db=name, **connection_params)
        logger.debug('New Database connection')

        database = self.client_connection[name]
        self.djongo_connection = DjongoClient(database, es)
        return self.client_connection[name]

    def _set_autocommit(self, autocommit):
        """
        Default method must be overridden, eventhough not used.

        TODO: For future reference, setting two phase commits and rollbacks
        might require populating this method.
        """
        pass

    def init_connection_state(self):
        try:
            dictConfig(self.settings_dict['LOGGING'])
        except KeyError:
            pass

    def create_cursor(self, name=None):
        """
        Returns an active connection cursor to the database.
        """
        return Cursor(self.client_connection, self.connection, self.djongo_connection)

    def _close(self):
        """
        Closes the client connection to the database.
        """
        if self.connection:
            with self.wrap_database_errors:
                self.connection.client.close()
                logger.debug('MongoClient connection closed')

    def _rollback(self):
        raise Error

    def _commit(self):
        """
        Commit routine

        TODO: two phase commits are not supported yet.
        """
        pass
