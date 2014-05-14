"""
Mixin defining common Studio functionality
"""

import datetime
import dateutil.parser
import logging
import time

from pytz import UTC

from xblock.fields import Scope, Field, Integer, XBlockMixin

log = logging.getLogger(__name__)


class DateTuple(Field):
    """
    Field that stores datetime objects as time tuples
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
            log.warning("Field {0} is missing month or day".format(self._name, field))
            return None
        if result.tzinfo is None:
            result = result.replace(tzinfo=UTC)
        return result

    def from_json(self, value):
        if value is None:
            return None

        return datetime.datetime(*value[0:6]).replace(tzinfo=UTC)

    def to_json(self, value):
        if value is None:
            return None

        return list(value.timetuple())

    def enforce_type(self, value):
        if value == "" or value is None:
            return None

        if isinstance(value, datetime.datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            return value

        if isinstance(value, tuple):
            return datetime.datetime(*value[0:6]).replace(tzinfo=UTC)

        if isinstance(value, time.struct_time):
            return datetime.datetime.fromtimestamp(time.mktime(value), UTC)

        if isinstance(value, basestring):
            return self._parse_date_wo_default_month_day(value)

        raise TypeError("Value should be datetime, timetuple, str or None, not {}".format(type(value)))


class CmsBlockMixin(XBlockMixin):
    """
    Mixin with fields common to all blocks in Studio
    """
    published_date = DateTuple(help="Date when the module was published", scope=Scope.settings)
    published_by = Integer(help="Id of the user who published this module", scope=Scope.settings)
