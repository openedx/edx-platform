"""
Custom fields for use in the coursewarehistoryextended django app.
"""

from django.db.models.fields import AutoField
from django.db.models.fields.related import OneToOneField


class UnsignedBigIntAutoField(AutoField):
    """
    An unsigned 8-byte integer for auto-incrementing primary keys.
    """
    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return "bigint UNSIGNED AUTO_INCREMENT"
        elif connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3':
            # Sqlite will only auto-increment the ROWID column. Any INTEGER PRIMARY KEY column
            # is an alias for that (https://www.sqlite.org/autoinc.html). An unsigned integer
            # isn't an alias for ROWID, so we have to give up on the unsigned part.
            return "integer"
        elif connection.settings_dict['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
            # Pg's bigserial is implicitly unsigned (doesn't allow negative numbers) and
            # goes 1-9.2x10^18
            return "BIGSERIAL"
        else:
            return None

    # rel_db_type was added in Django 1.10. For versions before, use UnsignedBigIntOneToOneField.
    def rel_db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return "bigint UNSIGNED"
        elif connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3':
            return "integer"
        elif connection.settings_dict['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
            return "BIGSERIAL"
        else:
            return None


class UnsignedBigIntOneToOneField(OneToOneField):
    """
    An unsigned 8-byte integer one-to-one foreign key to a unsigned 8-byte integer id field.

    Should only be necessary for versions of Django < 1.10.
    """
    def db_type(self, connection):
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
            return "bigint UNSIGNED"
        elif connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3':
            return "integer"
        elif connection.settings_dict['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
            return "BIGSERIAL"
        else:
            return None
