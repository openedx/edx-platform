"""Tests for classes defined in fields.py."""
import datetime
import unittest
from xmodule.fields import Date, StringyFloat, StringyInteger, StringyBoolean
from django.utils.timezone import UTC

class DateTest(unittest.TestCase):
    date = Date()

    def compare_dates(self, dt1, dt2, expected_delta):
        self.assertEqual(dt1 - dt2, expected_delta, str(dt1) + "-"
                                                    + str(dt2) + "!=" + str(expected_delta))

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
            datetime.datetime(current.year, 3, 12, 12, tzinfo=UTC()),
            DateTest.date.from_json("March 12 12:00"))
        self.assertEqual(
            datetime.datetime(current.year, 12, 4, 16, 30, tzinfo=UTC()),
            DateTest.date.from_json("December 4 16:30"))

    def test_to_json(self):
        '''
        Test converting time reprs to iso dates
        '''
        self.assertEqual(
            DateTest.date.to_json(
                datetime.datetime.strptime("2012-12-31T23:59:59Z", "%Y-%m-%dT%H:%M:%SZ")),
            "2012-12-31T23:59:59Z")
        self.assertEqual(
            DateTest.date.to_json(
                DateTest.date.from_json("2012-12-31T23:59:59Z")),
            "2012-12-31T23:59:59Z")
        self.assertEqual(
            DateTest.date.to_json(
                DateTest.date.from_json("2012-12-31T23:00:01-01:00")),
            "2012-12-31T23:00:01-01:00")


class StringyIntegerTest(unittest.TestCase):
    def assertEquals(self, expected, arg):
        self.assertEqual(expected, StringyInteger().from_json(arg))

    def test_integer(self):
        self.assertEquals(5, '5')
        self.assertEquals(0, '0')
        self.assertEquals(-1023, '-1023')

    def test_none(self):
        self.assertEquals(None, None)
        self.assertEquals(None, 'abc')
        self.assertEquals(None, '[1]')
        self.assertEquals(None, '1.023')


class StringyFloatTest(unittest.TestCase):

    def assertEquals(self, expected, arg):
        self.assertEqual(expected, StringyFloat().from_json(arg))

    def test_float(self):
        self.assertEquals(.23, '.23')
        self.assertEquals(5, '5')
        self.assertEquals(0, '0.0')
        self.assertEquals(-1023.22, '-1023.22')

    def test_none(self):
        self.assertEquals(None, None)
        self.assertEquals(None, 'abc')
        self.assertEquals(None, '[1]')


class StringyBooleanTest(unittest.TestCase):

    def assertEquals(self, expected, arg):
        self.assertEqual(expected, StringyBoolean().from_json(arg))

    def test_false(self):
        self.assertEquals(False, "false")
        self.assertEquals(False, "False")
        self.assertEquals(False, "")
        self.assertEquals(False, "hahahahah")

    def test_true(self):
        self.assertEquals(True, "true")
        self.assertEquals(True, "TruE")

    def test_pass_through(self):
        self.assertEquals(123, 123)

