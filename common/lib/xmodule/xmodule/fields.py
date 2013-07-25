import time
import logging
import re

from xblock.core import ModelType
import datetime
import dateutil.parser

from pytz import UTC

log = logging.getLogger(__name__)


class Date(ModelType):
    '''
    Date fields know how to parse and produce json (iso) compatible formats. Converts to tz aware datetimes.
    '''
    # See note below about not defaulting these
    CURRENT_YEAR = datetime.datetime.now(UTC).year
    PREVENT_DEFAULT_DAY_MON_SEED1 = datetime.datetime(CURRENT_YEAR, 1, 1, tzinfo=UTC)
    PREVENT_DEFAULT_DAY_MON_SEED2 = datetime.datetime(CURRENT_YEAR, 2, 2, tzinfo=UTC)

    def _parse_date_wo_default_month_day(self, field):
        """
        Parse the field as an iso string but prevent dateutils from defaulting the day or month while
        allowing it to default the other fields.
        """
        # It's not trivial to replace dateutil b/c parsing timezones as Z, +03:30, -400 is hard in python
        # however, we don't want dateutil to default the month or day (but some tests at least expect
        # us to default year); so, we'll see if dateutil uses the defaults for these the hard way
        result = dateutil.parser.parse(field, default=self.PREVENT_DEFAULT_DAY_MON_SEED1)
        result_other = dateutil.parser.parse(field, default=self.PREVENT_DEFAULT_DAY_MON_SEED2)
        if result != result_other:
            log.warning("Field {0} is missing month or day".format(self._name, field))
            return None
        if result.tzinfo is None:
            result = result.replace(tzinfo=UTC)
        return result

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
            return self._parse_date_wo_default_month_day(field)
        elif isinstance(field, (int, long, float)):
            return datetime.datetime.fromtimestamp(field / 1000, UTC)
        elif isinstance(field, time.struct_time):
            return datetime.datetime.fromtimestamp(time.mktime(field), UTC)
        elif isinstance(field, datetime.datetime):
            return field
        else:
            msg = "Field {0} has bad value '{1}'".format(
                self._name, field)
            raise TypeError(msg)

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
        else:
            raise TypeError("Cannot convert {} to json".format(value))

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
