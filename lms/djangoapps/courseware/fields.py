"""
Custom fields for use in the courseware django app.
"""

from django.db.models.fields import AutoField
from south.modelsinspector import add_introspection_rules


add_introspection_rules([], [r"^courseware\.fields\.UnsignedBigIntAutoField"])


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
        else:
            return None
