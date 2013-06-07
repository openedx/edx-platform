import time
import logging
import re

from xblock.core import ModelType
import datetime
import dateutil.parser

from xblock.core import Integer, Float, Boolean
from django.utils.timezone import UTC

log = logging.getLogger(__name__)


class Date(ModelType):
    '''
    Date fields know how to parse and produce json (iso) compatible formats. Converts to tz aware datetimes.
    '''
    def from_json(self, field):
        """
        Parse an optional metadata key containing a time: if present, complain
        if it doesn't parse.
        Return None if not present or invalid.
        """
        if field is None:
            return field
        elif field is "":
            return None
        elif isinstance(field, basestring):
            result = dateutil.parser.parse(field)
            if result.tzinfo is None:
                result = result.replace(tzinfo=UTC())
            return result
        elif isinstance(field, (int, long, float)):
            return datetime.datetime.fromtimestamp(field / 1000, UTC())
        elif isinstance(field, time.struct_time):
            return datetime.datetime.fromtimestamp(time.mktime(field), UTC())
        elif isinstance(field, datetime.datetime):
            return field
        else:
            msg = "Field {0} has bad value '{1}'".format(
                self._name, field)
            log.warning(msg)
            return None

    def to_json(self, value):
        """
        Convert a time struct to a string
        """
        if value is None:
            return None
        if isinstance(value, time.struct_time):
            # struct_times are always utc
            return time.strftime('%Y-%m-%dT%H:%M:%SZ', value)
        elif isinstance(value, datetime.datetime):
            if value.tzinfo is None or value.utcoffset().total_seconds() == 0:
                # isoformat adds +00:00 rather than Z
                return value.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                return value.isoformat()


TIMEDELTA_REGEX = re.compile(r'^((?P<days>\d+?) day(?:s?))?(\s)?((?P<hours>\d+?) hour(?:s?))?(\s)?((?P<minutes>\d+?) minute(?:s)?)?(\s)?((?P<seconds>\d+?) second(?:s)?)?$')


class Timedelta(ModelType):
    def from_json(self, time_str):
        """
        time_str: A string with the following components:
            <D> day[s] (optional)
            <H> hour[s] (optional)
            <M> minute[s] (optional)
            <S> second[s] (optional)

        Returns a datetime.timedelta parsed from the string
        """
        if time_str is None:
            return None
        parts = TIMEDELTA_REGEX.match(time_str)
        if not parts:
            return
        parts = parts.groupdict()
        time_params = {}
        for (name, param) in parts.iteritems():
            if param:
                time_params[name] = int(param)
        return datetime.timedelta(**time_params)

    def to_json(self, value):
        values = []
        for attr in ('days', 'hours', 'minutes', 'seconds'):
            cur_value = getattr(value, attr, 0)
            if cur_value > 0:
                values.append("%d %s" % (cur_value, attr))
        return ' '.join(values)


class StringyInteger(Integer):
    """
    A model type that converts from strings to integers when reading from json.
    If value does not parse as an int, returns None.
    """
    def from_json(self, value):
        try:
            return int(value)
        except Exception:
            return None


class StringyFloat(Float):
    """
    A model type that converts from string to floats when reading from json.
    If value does not parse as a float, returns None.
    """
    def from_json(self, value):
        try:
            return float(value)
        except:
            return None


class StringyBoolean(Boolean):
    """
    Reads strings from JSON as booleans.

    If the string is 'true' (case insensitive), then return True,
    otherwise False.

    JSON values that aren't strings are returned as-is.
    """
    def from_json(self, value):
        if isinstance(value, basestring):
            return value.lower() == 'true'
        return value
