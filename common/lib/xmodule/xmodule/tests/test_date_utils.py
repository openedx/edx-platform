# Tests for xmodule.util.date_utils

from nose.tools import assert_equals
from xmodule.util import date_utils
import datetime
from pytz import UTC


def test_get_default_time_display():
    assert_equals("", date_utils.get_default_time_display(None))
    test_time = datetime.datetime(1992, 3, 12, 15, 3, 30, tzinfo=UTC)
    assert_equals(
        "Mar 12, 1992 at 15:03 UTC",
        date_utils.get_default_time_display(test_time))
    assert_equals(
        "Mar 12, 1992 at 15:03 UTC",
        date_utils.get_default_time_display(test_time, True))
    assert_equals(
        "Mar 12, 1992 at 15:03",
        date_utils.get_default_time_display(test_time, False))

def test_get_default_time_display_notz():
    test_time = datetime.datetime(1992, 3, 12, 15, 3, 30)
    assert_equals(
        "Mar 12, 1992 at 15:03 UTC",
        date_utils.get_default_time_display(test_time))
    assert_equals(
        "Mar 12, 1992 at 15:03 UTC",
        date_utils.get_default_time_display(test_time, True))
    assert_equals(
        "Mar 12, 1992 at 15:03",
        date_utils.get_default_time_display(test_time, False))

# pylint: disable=W0232
class NamelessTZ(datetime.tzinfo):

    def utcoffset(self, _dt):
        return datetime.timedelta(hours=-3)

    def dst(self, _dt):
        return datetime.timedelta(0)

def test_get_default_time_display_no_tzname():
    assert_equals("", date_utils.get_default_time_display(None))
    test_time = datetime.datetime(1992, 3, 12, 15, 3, 30, tzinfo=NamelessTZ())
    assert_equals(
        "Mar 12, 1992 at 15:03-0300",
        date_utils.get_default_time_display(test_time))
    assert_equals(
        "Mar 12, 1992 at 15:03-0300",
        date_utils.get_default_time_display(test_time, True))
    assert_equals(
        "Mar 12, 1992 at 15:03",
        date_utils.get_default_time_display(test_time, False))
