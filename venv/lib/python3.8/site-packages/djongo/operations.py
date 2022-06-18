import pytz
from django.conf import settings
from django.db.backends.base.operations import BaseDatabaseOperations
from django.utils import timezone
import bson
import datetime
import calendar


class DatabaseOperations(BaseDatabaseOperations):

    def quote_name(self, name):
        if name.startswith('"') and name.endswith('"'):
            return name
        return '"{}"'.format(name)

    def adapt_datefield_value(self, value):
        if value is None:
            return None

        if isinstance(value, datetime.datetime) and timezone.is_aware(value):
            raise ValueError(
                "Djongo backend does not support timezone-aware dates.")

        x = calendar.timegm(value.timetuple())
        # this is presuming that UTC info is needed; anything after 'replace'
        # can be deleted for 'dt' if not.
        dt = datetime.datetime(1970, 1, 1).replace(
            tzinfo=datetime.timezone.utc)
        if x < 0:
            return dt + datetime.timedelta(seconds=x)
        else:
            return datetime.datetime.utcfromtimestamp(calendar.timegm(
                value.timetuple()))

    def adapt_datetimefield_value(self, value):
        if value is None:
            return None

        if isinstance(value, datetime.datetime) and timezone.is_aware(value):
            if settings.USE_TZ:
                value = timezone.make_naive(value, self.connection.timezone)
            else:
                raise ValueError(
                    "Djongo backend does not support timezone-aware datetimes when USE_TZ is False.")
        return value

    def adapt_timefield_value(self, value):
        if value is None:
            return None

        if isinstance(value, str):
            return datetime.datetime.strptime(value, '%H:%M:%S')

        if timezone.is_aware(value):
            raise ValueError(
                "Djongo backend does not support timezone-aware times.")

        return datetime.datetime(1900, 1, 1, value.hour, value.minute,
                                 value.second, value.microsecond)
    
    def adapt_decimalfield_value(self, value, max_digits=None, decimal_places=None):
        if value is None:
            return None
        return bson.Decimal128(super().adapt_decimalfield_value(value, max_digits, decimal_places))

    def convert_datefield_value(self, value, expression, connection):
        if isinstance(value, datetime.datetime):
            if settings.USE_TZ:
                value = timezone.make_aware(value, self.connection.timezone)
            value = value.date()
        return value

    def convert_timefield_value(self, value, expression, connection):
        if isinstance(value, datetime.datetime):
            if settings.USE_TZ:
                value = timezone.make_aware(value, self.connection.timezone)
            value = value.time()
        return value

    def convert_datetimefield_value(self, value, expression, connection):
        if isinstance(value, datetime.datetime):
            if settings.USE_TZ:
                value = timezone.make_aware(value, self.connection.timezone)
        return value

    def get_db_converters(self, expression):
        converters = super(DatabaseOperations,
                           self).get_db_converters(expression)
        internal_type = expression.output_field.get_internal_type()
        if internal_type == 'DateField':
            converters.append(self.convert_datefield_value)
        elif internal_type == 'TimeField':
            converters.append(self.convert_timefield_value)
        elif internal_type == 'DateTimeField':
            converters.append(self.convert_datetimefield_value)
        return converters

    def sql_flush(self, style, tables, reset_sequences, allow_cascade=False):
        # TODO: Need to implement this fully
        return [f'ALTER TABLE "{table}" FLUSH'
                for table in tables]

    def max_name_length(self):
        return 60

    def no_limit_value(self):
        return None

    def bulk_insert_sql(self, fields, placeholder_rows):
        return ' '.join(
            'VALUES (%s)' % ', '.join(row)
            for row in placeholder_rows
        )

    def date_extract_sql(self, lookup_type, field_name):
        return "EXTRACT('%s' FROM %s)" % (lookup_type, field_name)

    def date_trunc_sql(self, lookup_type, field_name):
        return "DATE_TRUNC('%s', %s)" % (lookup_type, field_name)
