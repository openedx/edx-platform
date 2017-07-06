import time
import logging
import re

from xblock.fields import JSONField
import datetime
import dateutil.parser

from pytz import UTC

log = logging.getLogger(__name__)


class Date(JSONField):
    '''
    Date fields know how to parse and produce json (iso) compatible formats. Converts to tz aware datetimes.
    '''
    # See note below about not defaulting these
    CURRENT_YEAR = datetime.datetime.now(UTC).year
    PREVENT_DEFAULT_DAY_MON_SEED1 = datetime.datetime(CURRENT_YEAR, 1, 1, tzinfo=UTC)
    PREVENT_DEFAULT_DAY_MON_SEED2 = datetime.datetime(CURRENT_YEAR, 2, 2, tzinfo=UTC)

    MUTABLE = False

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
            log.warning("Field {0} is missing month or day".format(self.name))
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
                self.name, field)
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
                if value.year < 1900:
                    # strftime doesn't work for pre-1900 dates, so use
                    # isoformat instead
                    return value.isoformat()
                # isoformat adds +00:00 rather than Z
                return value.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                return value.isoformat()
        else:
            raise TypeError("Cannot convert {!r} to json".format(value))

    enforce_type = from_json

TIMEDELTA_REGEX = re.compile(r'^((?P<days>\d+?) day(?:s?))?(\s)?((?P<hours>\d+?) hour(?:s?))?(\s)?((?P<minutes>\d+?) minute(?:s)?)?(\s)?((?P<seconds>\d+?) second(?:s)?)?$')


class Timedelta(JSONField):
    # Timedeltas are immutable, see http://docs.python.org/2/library/datetime.html#available-types
    MUTABLE = False

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

        if isinstance(time_str, datetime.timedelta):
            return time_str

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
        if value is None:
            return None

        values = []
        for attr in ('days', 'hours', 'minutes', 'seconds'):
            cur_value = getattr(value, attr, 0)
            if cur_value > 0:
                values.append("%d %s" % (cur_value, attr))
        return ' '.join(values)

    def enforce_type(self, value):
        """
        Ensure that when set explicitly the Field is set to a timedelta
        """
        if isinstance(value, datetime.timedelta) or value is None:
            return value

        return self.from_json(value)


class RelativeTime(JSONField):
    """
    Field for start_time and end_time video module properties.

    It was decided, that python representation of start_time and end_time
    should be python datetime.timedelta object, to be consistent with
    common time representation.

    At the same time, serialized representation should be "HH:MM:SS"
    This format is convenient to use in XML (and it is used now),
    and also it is used in frond-end studio editor of video module as format
    for start and end time fields.

    In database we previously had float type for start_time and end_time fields,
    so we are checking it also.

    Python object of RelativeTime is datetime.timedelta.
    JSONed representation of RelativeTime is "HH:MM:SS"
    """
    # Timedeltas are immutable, see http://docs.python.org/2/library/datetime.html#available-types
    MUTABLE = False

    @classmethod
    def isotime_to_timedelta(cls, value):
        """
        Validate that value in "HH:MM:SS" format and convert to timedelta.

        Validate that user, that edits XML, sets proper format, and
         that max value that can be used by user is "23:59:59".
        """
        try:
            obj_time = time.strptime(value, '%H:%M:%S')
        except ValueError as e:
            raise ValueError(
                "Incorrect RelativeTime value {!r} was set in XML or serialized. "
                "Original parse message is {}".format(value, e.message)
            )
        return datetime.timedelta(
            hours=obj_time.tm_hour,
            minutes=obj_time.tm_min,
            seconds=obj_time.tm_sec
        )

    def from_json(self, value):
        """
        Convert value is in 'HH:MM:SS' format to datetime.timedelta.

        If not value, returns 0.
        If value is float (backward compatibility issue), convert to timedelta.
        """
        if not value:
            return datetime.timedelta(seconds=0)

        if isinstance(value, datetime.timedelta):
            return value

        # We've seen serialized versions of float in this field
        if isinstance(value, float):
            return datetime.timedelta(seconds=value)

        if isinstance(value, basestring):
            return self.isotime_to_timedelta(value)

        msg = "RelativeTime Field {0} has bad value '{1!r}'".format(self.name, value)
        raise TypeError(msg)

    def to_json(self, value):
        """
        Convert datetime.timedelta to "HH:MM:SS" format.

        If not value, return "00:00:00"

        Backward compatibility: check if value is float, and convert it. No exceptions here.

        If value is not float, but is exceed 23:59:59, raise exception.
        """
        if not value:
            return "00:00:00"

        if isinstance(value, float):  # backward compatibility
            value = min(value, 86400)
            return self.timedelta_to_string(datetime.timedelta(seconds=value))

        if isinstance(value, datetime.timedelta):
            if value.total_seconds() > 86400:  # sanity check
                raise ValueError(
                    "RelativeTime max value is 23:59:59=86400.0 seconds, "
                    "but {} seconds is passed".format(value.total_seconds())
                )
            return self.timedelta_to_string(value)

        raise TypeError("RelativeTime: cannot convert {!r} to json".format(value))

    def timedelta_to_string(self, value):
        """
        Makes first 'H' in str representation non-optional.

         str(timedelta) has [H]H:MM:SS format, which is not suitable
         for front-end (and ISO time standard), so we force HH:MM:SS format.
         """
        stringified = str(value)
        if len(stringified) == 7:
            stringified = '0' + stringified
        return stringified

    def enforce_type(self, value):
        """
        Ensure that when set explicitly the Field is set to a timedelta
        """
        if isinstance(value, datetime.timedelta) or value is None:
            return value

        return self.from_json(value)
