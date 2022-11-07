"""Tests for classes defined in fields.py."""


import datetime
import unittest
import pytest
from pytz import UTC

from xmodule.fields import Date, RelativeTime, Timedelta


class DateTest(unittest.TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring
    date = Date()

    def compare_dates(self, dt1, dt2, expected_delta):
        assert (dt1 - dt2) == expected_delta, ((((str(dt1) + '-') + str(dt2)) + '!=') + str(expected_delta))

    def test_from_json(self):
        """Test conversion from iso compatible date strings to struct_time"""
        self.compare_dates(
            DateTest.date.from_json("2013-01-01"),
            DateTest.date.from_json("2012-12-31"),
            datetime.timedelta(days=1)
        )
        self.compare_dates(
            DateTest.date.from_json("2013-01-01T00"),
            DateTest.date.from_json("2012-12-31T23"),
            datetime.timedelta(hours=1)
        )
        self.compare_dates(
            DateTest.date.from_json("2013-01-01T00:00"),
            DateTest.date.from_json("2012-12-31T23:59"),
            datetime.timedelta(minutes=1)
        )
        self.compare_dates(
            DateTest.date.from_json("2013-01-01T00:00:00"),
            DateTest.date.from_json("2012-12-31T23:59:59"),
            datetime.timedelta(seconds=1)
        )
        self.compare_dates(
            DateTest.date.from_json("2013-01-01T00:00:00Z"),
            DateTest.date.from_json("2012-12-31T23:59:59Z"),
            datetime.timedelta(seconds=1)
        )
        self.compare_dates(
            DateTest.date.from_json("2012-12-31T23:00:01-01:00"),
            DateTest.date.from_json("2013-01-01T00:00:00+01:00"),
            datetime.timedelta(hours=1, seconds=1)
        )

    def test_enforce_type(self):
        assert DateTest.date.enforce_type(None) is None
        assert DateTest.date.enforce_type('') is None
        assert DateTest.date.enforce_type('2012-12-31T23:00:01') ==\
               datetime.datetime(2012, 12, 31, 23, 0, 1, tzinfo=UTC)
        assert DateTest.date.enforce_type(1234567890000) == datetime.datetime(2009, 2, 13, 23, 31, 30, tzinfo=UTC)
        assert DateTest.date.enforce_type(datetime.datetime(2014, 5, 9, 21, 1, 27, tzinfo=UTC)) ==\
               datetime.datetime(2014, 5, 9, 21, 1, 27, tzinfo=UTC)
        with pytest.raises(TypeError):
            DateTest.date.enforce_type([1])

    def test_return_None(self):
        assert DateTest.date.from_json('') is None
        assert DateTest.date.from_json(None) is None
        with pytest.raises(TypeError):
            DateTest.date.from_json(['unknown value'])

    def test_old_due_date_format(self):
        current = datetime.datetime.today()
        assert datetime.datetime(current.year, 3, 12, 12, tzinfo=UTC) == DateTest.date.from_json('March 12 12:00')
        assert datetime.datetime(current.year, 12, 4, 16, 30, tzinfo=UTC) == DateTest.date.from_json('December 4 16:30')
        assert DateTest.date.from_json('12 12:00') is None

    def test_non_std_from_json(self):
        """
        Test the non-standard args being passed to from_json
        """
        now = datetime.datetime.now(UTC)
        delta = now - datetime.datetime.fromtimestamp(0, UTC)
        assert DateTest.date.from_json(delta.total_seconds() * 1000) == now
        yesterday = datetime.datetime.now(UTC) - datetime.timedelta(days=-1)
        assert DateTest.date.from_json(yesterday) == yesterday

    def test_to_json(self):
        """
        Test converting time reprs to iso dates
        """
        assert DateTest.date.to_json(datetime.datetime.strptime('2012-12-31T23:59:59Z', '%Y-%m-%dT%H:%M:%SZ')) ==\
               '2012-12-31T23:59:59Z'
        assert DateTest.date.to_json(DateTest.date.from_json('2012-12-31T23:59:59Z')) == '2012-12-31T23:59:59Z'
        assert DateTest.date.to_json(DateTest.date.from_json('2012-12-31T23:00:01-01:00')) ==\
               '2012-12-31T23:00:01-01:00'
        with pytest.raises(TypeError):
            DateTest.date.to_json('2012-12-31T23:00:01-01:00')


class TimedeltaTest(unittest.TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring
    delta = Timedelta()

    def test_from_json(self):
        assert TimedeltaTest.delta.from_json('1 day 12 hours 59 minutes 59 seconds') ==\
               datetime.timedelta(days=1, hours=12, minutes=59, seconds=59)

        assert TimedeltaTest.delta.from_json('1 day 46799 seconds') == datetime.timedelta(days=1, seconds=46799)

    def test_enforce_type(self):
        assert TimedeltaTest.delta.enforce_type(None) is None
        assert TimedeltaTest.delta.enforce_type(datetime.timedelta(days=1, seconds=46799)) ==\
               datetime.timedelta(days=1, seconds=46799)
        assert TimedeltaTest.delta.enforce_type('1 day 46799 seconds') == datetime.timedelta(days=1, seconds=46799)
        with pytest.raises(TypeError):
            TimedeltaTest.delta.enforce_type([1])

    def test_to_json(self):
        assert '1 days 46799 seconds' ==\
               TimedeltaTest.delta.to_json(datetime.timedelta(days=1, hours=12, minutes=59, seconds=59))


class RelativeTimeTest(unittest.TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    delta = RelativeTime()

    def test_from_json(self):
        assert RelativeTimeTest.delta.from_json('0:05:07') == datetime.timedelta(seconds=307)

        assert RelativeTimeTest.delta.from_json(100.0) == datetime.timedelta(seconds=100)
        assert RelativeTimeTest.delta.from_json(None) == datetime.timedelta(seconds=0)

        with pytest.raises(TypeError):
            RelativeTimeTest.delta.from_json(1234)  # int

        with pytest.raises(ValueError):
            RelativeTimeTest.delta.from_json("77:77:77")

    def test_enforce_type(self):
        assert RelativeTimeTest.delta.enforce_type(None) is None
        assert RelativeTimeTest.delta.enforce_type(datetime.timedelta(days=1, seconds=46799)) ==\
               datetime.timedelta(days=1, seconds=46799)
        assert RelativeTimeTest.delta.enforce_type('0:05:07') == datetime.timedelta(seconds=307)
        with pytest.raises(TypeError):
            RelativeTimeTest.delta.enforce_type([1])

    def test_to_json(self):
        assert '01:02:03' == RelativeTimeTest.delta.to_json(datetime.timedelta(seconds=3723))
        assert '00:00:00' == RelativeTimeTest.delta.to_json(None)
        assert '00:01:40' == RelativeTimeTest.delta.to_json(100.0)

        error_msg = "RelativeTime max value is 23:59:59=86400.0 seconds, but 90000.0 seconds is passed"
        with self.assertRaisesRegex(ValueError, error_msg):
            RelativeTimeTest.delta.to_json(datetime.timedelta(seconds=90000))

        with pytest.raises(TypeError):
            RelativeTimeTest.delta.to_json("123")

    def test_str(self):
        assert '01:02:03' == RelativeTimeTest.delta.to_json(datetime.timedelta(seconds=3723))
        assert '11:02:03' == RelativeTimeTest.delta.to_json(datetime.timedelta(seconds=39723))
