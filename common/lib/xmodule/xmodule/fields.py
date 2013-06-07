import time
import logging
import re

from datetime import timedelta
from xblock.core import ModelType
import datetime
import dateutil.parser

log = logging.getLogger(__name__)


class Date(ModelType):
    '''
    Date fields know how to parse and produce json (iso) compatible formats.
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
            d = dateutil.parser.parse(field)
            return d.utctimetuple()
        elif isinstance(field, (int, long, float)):
            return time.gmtime(field / 1000)
        elif isinstance(field, time.struct_time):
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
            return value.isoformat() + 'Z'


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
        parts = TIMEDELTA_REGEX.match(time_str)
        if not parts:
            return
        parts = parts.groupdict()
        time_params = {}
        for (name, param) in parts.iteritems():
            if param:
                time_params[name] = int(param)
        return timedelta(**time_params)

    def to_json(self, value):
        values = []
        for attr in ('days', 'hours', 'minutes', 'seconds'):
            cur_value = getattr(value, attr, 0)
            if cur_value > 0:
                values.append("%d %s" % (cur_value, attr))
        return ' '.join(values)
