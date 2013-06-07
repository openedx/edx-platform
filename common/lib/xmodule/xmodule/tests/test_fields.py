"""Tests for classes defined in fields.py."""
import datetime
import unittest
from django.utils.timezone import UTC
from xmodule.fields import Date
import time

class DateTest(unittest.TestCase):
    date = Date()

    @staticmethod
    def struct_to_datetime(struct_time):
        return datetime.datetime(struct_time.tm_year, struct_time.tm_mon,
            struct_time.tm_mday, struct_time.tm_hour,
            struct_time.tm_min, struct_time.tm_sec, tzinfo=UTC())

    def compare_dates(self, date1, date2, expected_delta):
        dt1 = DateTest.struct_to_datetime(date1)
        dt2 = DateTest.struct_to_datetime(date2)
        self.assertEqual(dt1 - dt2, expected_delta, str(date1) + "-"
                                                    + str(date2) + "!=" + str(expected_delta))

    def test_from_json(self):
        '''Test conversion from iso compatible date strings to struct_time'''
        self.compare_dates(
            DateTest.date.from_json("2013-01-01"),
            DateTest.date.from_json("2012-12-31"),
            datetime.timedelta(days=1))
        self.compare_dates(
            DateTest.date.from_json("2013-01-01T00"),
            DateTest.date.from_json("2012-12-31T23"),
            datetime.timedelta(hours=1))
        self.compare_dates(
            DateTest.date.from_json("2013-01-01T00:00"),
            DateTest.date.from_json("2012-12-31T23:59"),
            datetime.timedelta(minutes=1))
        self.compare_dates(
            DateTest.date.from_json("2013-01-01T00:00:00"),
            DateTest.date.from_json("2012-12-31T23:59:59"),
            datetime.timedelta(seconds=1))
        self.compare_dates(
            DateTest.date.from_json("2013-01-01T00:00:00Z"),
            DateTest.date.from_json("2012-12-31T23:59:59Z"),
            datetime.timedelta(seconds=1))
        self.compare_dates(
            DateTest.date.from_json("2012-12-31T23:00:01-01:00"),
            DateTest.date.from_json("2013-01-01T00:00:00+01:00"),
            datetime.timedelta(hours=1, seconds=1))

    def test_return_None(self):
        self.assertIsNone(DateTest.date.from_json(""))
        self.assertIsNone(DateTest.date.from_json(None))
        self.assertIsNone(DateTest.date.from_json(['unknown value']))

    def test_old_due_date_format(self):
        current = datetime.datetime.today()
        self.assertEqual(
            time.struct_time((current.year, 3, 12, 12, 0, 0, 1, 71, 0)),
            DateTest.date.from_json("March 12 12:00"))
        self.assertEqual(
            time.struct_time((current.year, 12, 4, 16, 30, 0, 2, 338, 0)),
            DateTest.date.from_json("December 4 16:30"))

    def test_to_json(self):
        '''
        Test converting time reprs to iso dates
        '''
        self.assertEqual(
            DateTest.date.to_json(
                time.strptime("2012-12-31T23:59:59Z", "%Y-%m-%dT%H:%M:%SZ")),
            "2012-12-31T23:59:59Z")
        self.assertEqual(
            DateTest.date.to_json(
                DateTest.date.from_json("2012-12-31T23:59:59Z")),
            "2012-12-31T23:59:59Z")
        self.assertEqual(
            DateTest.date.to_json(
                DateTest.date.from_json("2012-12-31T23:00:01-01:00")),
            "2013-01-01T00:00:01Z")

