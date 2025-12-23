"""Custom XBlock field types for handling dates, times, durations, and scores."""

import datetime
import logging
import re
import time

import dateutil.parser
from pytz import UTC
from xblock.fields import JSONField, List
from xblock.scorable import Score

log = logging.getLogger(__name__)


class Date(JSONField):
    """
    Date fields know how to parse and produce json (iso) compatible formats. Converts to tz aware datetimes.
    """

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
            log.warning("Field %s is missing month or day", self.name)
            return None
        if result.tzinfo is None:
            result = result.replace(tzinfo=UTC)
        return result

    def from_json(self, value):
        """
        Parse an optional metadata key containing a time: if present, complain
        if it doesn't parse.
        Return None if not present or invalid.
        """
        if value is None:
            return value

        if value == "":
            return None

        if isinstance(value, str):
            return self._parse_date_wo_default_month_day(value)

        if isinstance(value, (int, float)):
            return datetime.datetime.fromtimestamp(value / 1000, UTC)

        if isinstance(value, time.struct_time):
            return datetime.datetime.fromtimestamp(time.mktime(value), UTC)

        if isinstance(value, datetime.datetime):
            return value

        msg = f"value {self.name} has bad value '{value}'"
        raise TypeError(msg)

    def to_json(self, value):
        """
        Convert a time struct to a string
        """
        if value is None:
            return None

        if isinstance(value, time.struct_time):
            # struct_times are always utc
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", value)

        if isinstance(value, datetime.datetime):
            if value.tzinfo is None or value.utcoffset().total_seconds() == 0:
                if value.year < 1900:
                    # strftime doesn't work for pre-1900 dates, so use
                    # isoformat instead
                    return value.isoformat()
                # isoformat adds +00:00 rather than Z
                return value.strftime("%Y-%m-%dT%H:%M:%SZ")

            return value.isoformat()

        raise TypeError(f"Cannot convert {value!r} to json")

    enforce_type = from_json


TIMEDELTA_REGEX = re.compile(
    r"^((?P<days>\d+?) day(?:s?))?(\s)?"
    r"((?P<hours>\d+?) hour(?:s?))?(\s)?"
    r"((?P<minutes>\d+?) minute(?:s)?)?(\s)?"
    r"((?P<seconds>\d+?) second(?:s)?)?$"
)


class Timedelta(JSONField):
    """Field type for serializing/deserializing timedelta values to/from human-readable strings."""

    # Timedeltas are immutable, see https://docs.python.org/3/library/datetime.html#available-types
    MUTABLE = False

    def from_json(self, value):
        """
        value: A string with the following components:
            <D> day[s] (optional)
            <H> hour[s] (optional)
            <M> minute[s] (optional)
            <S> second[s] (optional)

        Returns a datetime.timedelta parsed from the string
        """
        if value is None:
            return None

        if isinstance(value, datetime.timedelta):
            return value

        parts = TIMEDELTA_REGEX.match(value)
        if not parts:
            return None
        parts = parts.groupdict()
        time_params = {}
        for name, param in parts.items():
            if param:
                time_params[name] = int(param)
        return datetime.timedelta(**time_params)

    def to_json(self, value):
        """Serialize a datetime.timedelta object into a human-readable string."""
        if value is None:
            return None

        values = []
        for attr in ("days", "hours", "minutes", "seconds"):
            cur_value = getattr(value, attr, 0)
            if cur_value > 0:
                values.append(f"{cur_value} {attr}")
        return " ".join(values)

    def enforce_type(self, value):
        """
        Ensure that when set explicitly the Field is set to a timedelta
        """
        if isinstance(value, datetime.timedelta) or value is None:
            return value

        return self.from_json(value)


class RelativeTime(JSONField):
    """
    Field for start_time and end_time video block properties.

    It was decided, that python representation of start_time and end_time
    should be python datetime.timedelta object, to be consistent with
    common time representation.

    At the same time, serialized representation should be "HH:MM:SS"
    This format is convenient to use in XML (and it is used now),
    and also it is used in frond-end studio editor of video block as format
    for start and end time fields.

    In database we previously had float type for start_time and end_time fields,
    so we are checking it also.

    Python object of RelativeTime is datetime.timedelta.
    JSONed representation of RelativeTime is "HH:MM:SS"
    """

    # Timedeltas are immutable, see https://docs.python.org/3/library/datetime.html#available-types
    MUTABLE = False

    @classmethod
    def isotime_to_timedelta(cls, value):
        """
        Validate that value in "HH:MM:SS" format and convert to timedelta.

        Validate that user, that edits XML, sets proper format, and
         that max value that can be used by user is "23:59:59".
        """
        try:
            obj_time = time.strptime(value, "%H:%M:%S")
        except ValueError as e:
            raise ValueError(
                f"Incorrect RelativeTime value {value!r} was set in XML or serialized. Original parse message is {e}"
            ) from e
        return datetime.timedelta(hours=obj_time.tm_hour, minutes=obj_time.tm_min, seconds=obj_time.tm_sec)

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

        if isinstance(value, str):
            return self.isotime_to_timedelta(value)

        msg = f"RelativeTime Field {self.name} has bad value '{value!r}'"
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
                    f"RelativeTime max value is 23:59:59=86400.0 seconds, but {value.total_seconds()} seconds is passed"
                )
            return self.timedelta_to_string(value)

        raise TypeError(f"RelativeTime: cannot convert {value!r} to json")

    def timedelta_to_string(self, value):
        """
        Makes first 'H' in str representation non-optional.

         str(timedelta) has [H]H:MM:SS format, which is not suitable
         for front-end (and ISO time standard), so we force HH:MM:SS format.
        """
        stringified = str(value)
        if len(stringified) == 7:
            stringified = "0" + stringified
        return stringified

    def enforce_type(self, value):
        """
        Ensure that when set explicitly the Field is set to a timedelta
        """
        if isinstance(value, datetime.timedelta) or value is None:
            return value

        return self.from_json(value)


class ScoreField(JSONField):  # pylint: disable=too-few-public-methods
    """
    Field for blocks that need to store a Score. XBlocks that implement
    the ScorableXBlockMixin may need to store their score separately
    from their problem state, specifically for use in staff override
    of problem scores.
    """

    MUTABLE = False

    def from_json(self, value):
        """Deserialize a dict with 'raw_earned' and 'raw_possible' into a Score object, validating values."""
        if value is None:
            return value
        if isinstance(value, Score):
            return value

        if set(value) != {"raw_earned", "raw_possible"}:
            raise TypeError(f"Scores must contain only a raw earned and raw possible value. Got {set(value)}")

        raw_earned = value["raw_earned"]
        raw_possible = value["raw_possible"]

        if raw_possible < 0:
            raise ValueError(
                f"Error deserializing field of type {self.display_name}: "
                f"Expected a positive number for raw_possible, got {raw_possible}."
            )

        if not 0 <= raw_earned <= raw_possible:
            raise ValueError(
                f"Error deserializing field of type {self.display_name}: "
                f"Expected raw_earned between 0 and {raw_possible}, got {raw_earned}."
            )

        return Score(raw_earned, raw_possible)

    enforce_type = from_json


class ListScoreField(ScoreField, List):  # pylint: disable=too-few-public-methods
    """
    Field for blocks that need to store a list of Scores.
    """

    MUTABLE = True
    _default = []

    def from_json(self, value):
        if value is None:
            return value
        if isinstance(value, list):
            scores = []
            for score_json in value:
                score = super().from_json(score_json)
                scores.append(score)
            return scores

        raise TypeError(f"Value must be a list of Scores. Got {type(value)}")

    enforce_type = from_json
