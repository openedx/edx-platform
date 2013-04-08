# Tests for xmodule.util.date_utils

from nose.tools import assert_equals
from xmodule.util import date_utils
import datetime
import time


def test_get_time_struct_display():
    assert_equals("", date_utils.get_time_struct_display(None, ""))
    test_time = time.struct_time((1992, 3, 12, 15, 3, 30, 1, 71, 0))
    assert_equals("03/12/1992", date_utils.get_time_struct_display(test_time, '%m/%d/%Y'))
    assert_equals("15:03", date_utils.get_time_struct_display(test_time, '%H:%M'))


def test_get_default_time_display():
    assert_equals("", date_utils.get_default_time_display(None))
    test_time = time.struct_time((1992, 3, 12, 15, 3, 30, 1, 71, 0))
    assert_equals(
        "Mar 12, 1992 at 15:03 UTC",
        date_utils.get_default_time_display(test_time))
    assert_equals(
        "Mar 12, 1992 at 15:03 UTC",
        date_utils.get_default_time_display(test_time, True))
    assert_equals(
        "Mar 12, 1992 at 15:03",
        date_utils.get_default_time_display(test_time, False))


def test_time_to_datetime():
    assert_equals(None, date_utils.time_to_datetime(None))
    test_time = time.struct_time((1992, 3, 12, 15, 3, 30, 1, 71, 0))
    assert_equals(
        datetime.datetime(1992, 3, 12, 15, 3, 30),
        date_utils.time_to_datetime(test_time))
