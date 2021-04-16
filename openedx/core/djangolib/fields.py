"""
Custom Django fields.
"""

from django.db import models


class CharNullField(models.CharField):
    """
    CharField that stores NULL but returns ''
    """

    description = "CharField that stores NULL but returns ''"

    def to_python(self, value):
        """Converts the value into the correct Python object."""
        if isinstance(value, models.CharField):
            return value
        if value is None:
            return ""
        else:
            return value

    def get_db_prep_value(self, value, connection, prepared=False):
        """Converts value to a backend-specific value."""
        if not prepared:
            value = self.get_prep_value(value)
        if value == "":
            return None
        else:
            return value


class BigAutoField(models.AutoField):
    """
    AutoField that uses BigIntegers.

    This exists in Django as of version 1.10.
    """

    def db_type(self, connection):
        """
        The type of the field to insert into the database.
        """
        conn_module = type(connection).__module__
        if "mysql" in conn_module:
            return "bigint AUTO_INCREMENT"
        elif "postgres" in conn_module:
            return "bigserial"
        else:
            return super().db_type(connection)

    def rel_db_type(self, connection):
        """
        The type to be used by relations pointing to this field.

        Not used until Django 1.10.
        """
        return "bigint"
