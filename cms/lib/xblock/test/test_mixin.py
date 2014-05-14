import unittest
import datetime
import time

from pytz import UTC

from cms.lib.xblock.mixin import DateTuple

class DateTupleTest(unittest.TestCase):
    datetuple = DateTuple()

    def test_from_json(self):
        '''Test conversion from iso compatible date strings to struct_time'''
        self.assertEqual(
            DateTupleTest.datetuple.from_json((2014, 5, 9, 21, 1, 27)),
            datetime.datetime(2014, 5, 9, 21, 1, 27, tzinfo=UTC))
        self.assertIsNone(DateTupleTest.datetuple.from_json(None))

    def test_enforce_type(self):
        self.assertEqual(DateTupleTest.datetuple.enforce_type(
            (2014, 5, 9, 21, 1, 27)),
            datetime.datetime(2014, 5, 9, 21, 1, 27, tzinfo=UTC))
        self.assertEqual(DateTupleTest.datetuple.enforce_type(
            time.struct_time((2014, 5, 9, 21, 1, 27, 0, 0, 0))),
            datetime.datetime(2014, 5, 9, 21, 1, 27, tzinfo=UTC))
        self.assertEqual(DateTupleTest.datetuple.enforce_type(
            datetime.datetime(2014, 5, 9, 21, 1, 27)),
            datetime.datetime(2014, 5, 9, 21, 1, 27, tzinfo=UTC))
        self.assertEqual(DateTupleTest.datetuple.enforce_type(
            "2013-01-01T00:00:00Z"),
            datetime.datetime(2013, 1, 1, 00, 00, 00, tzinfo=UTC))
        self.assertEqual(DateTupleTest.datetuple.enforce_type(
            "2013-01-01 11:44:22"),
            datetime.datetime(2013, 1, 1, 11, 44, 22, tzinfo=UTC))
        self.assertEqual(DateTupleTest.datetuple.enforce_type(
            "2012-12-31T23:59"),
            datetime.datetime(2012, 12, 31, 23, 59, 00, tzinfo=UTC))
        self.assertIsNone(DateTupleTest.datetuple.enforce_type(None))
        self.assertIsNone(DateTupleTest.datetuple.enforce_type(""))

    def test_to_json(self):
        self.assertEqual(DateTupleTest.datetuple.to_json(
            datetime.datetime(2014, 5, 9, 21, 1, 27, tzinfo=UTC))[:6],
            [2014, 5, 9, 21, 1, 27])
        self.assertIsNone(DateTupleTest.datetuple.to_json(None))
