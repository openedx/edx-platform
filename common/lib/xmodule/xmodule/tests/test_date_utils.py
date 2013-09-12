"""Tests for xmodule.util.date_utils"""

from nose.tools import assert_equals, assert_false  # pylint: disable=E0611
from xmodule.util.date_utils import get_default_time_display, get_time_display, almost_same_datetime
from datetime import datetime, timedelta, tzinfo
from pytz import UTC


def test_get_default_time_display():
    assert_equals("", get_default_time_display(None))
    test_time = datetime(1992, 3, 12, 15, 3, 30, tzinfo=UTC)
    assert_equals(
        "Mar 12, 1992 at 15:03 UTC",
        get_default_time_display(test_time))


def test_get_dflt_time_disp_notz():
    test_time = datetime(1992, 3, 12, 15, 3, 30)
    assert_equals(
        "Mar 12, 1992 at 15:03 UTC",
        get_default_time_display(test_time))


def test_get_time_disp_ret_empty():
    assert_equals("", get_time_display(None))
    test_time = datetime(1992, 3, 12, 15, 3, 30, tzinfo=UTC)
    assert_equals("", get_time_display(test_time, ""))


def test_get_time_display():
    test_time = datetime(1992, 3, 12, 15, 3, 30, tzinfo=UTC)
    assert_equals("dummy text", get_time_display(test_time, 'dummy text'))
    assert_equals("Mar 12 1992", get_time_display(test_time, '%b %d %Y'))
    assert_equals("Mar 12 1992 UTC", get_time_display(test_time, '%b %d %Y %Z'))
    assert_equals("Mar 12 15:03", get_time_display(test_time, '%b %d %H:%M'))


def test_get_time_pass_through():
    test_time = datetime(1992, 3, 12, 15, 3, 30, tzinfo=UTC)
    assert_equals("Mar 12, 1992 at 15:03 UTC", get_time_display(test_time))
    assert_equals("Mar 12, 1992 at 15:03 UTC", get_time_display(test_time, None))
    assert_equals("Mar 12, 1992 at 15:03 UTC", get_time_display(test_time, "%"))


# pylint: disable=W0232
class NamelessTZ(tzinfo):
    """Static timezone for testing"""

    def utcoffset(self, _dt):
        return timedelta(hours=-3)

    def dst(self, _dt):
        return timedelta(0)


def test_get_default_time_display_no_tzname():
    assert_equals("", get_default_time_display(None))
    test_time = datetime(1992, 3, 12, 15, 3, 30, tzinfo=NamelessTZ())
    assert_equals(
        "Mar 12, 1992 at 15:03-0300",
        get_default_time_display(test_time))


def test_almost_same_datetime():
    assert almost_same_datetime(
        datetime(2013, 5, 3, 10, 20, 30),
        datetime(2013, 5, 3, 10, 21, 29)
    )

    assert almost_same_datetime(
        datetime(2013, 5, 3, 11, 20, 30),
        datetime(2013, 5, 3, 10, 21, 29),
        timedelta(hours=1)
    )

    assert_false(
        almost_same_datetime(
            datetime(2013, 5, 3, 11, 20, 30),
            datetime(2013, 5, 3, 10, 21, 29)
        )
    )

    assert_false(
        almost_same_datetime(
            datetime(2013, 5, 3, 11, 20, 30),
            datetime(2013, 5, 3, 10, 21, 29),
            timedelta(minutes=10)
        )
    )
