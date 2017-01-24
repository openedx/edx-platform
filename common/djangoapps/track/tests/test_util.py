from datetime import datetime
import json

from pytz import UTC

from django.test import TestCase

from track.utils import DateTimeJSONEncoder


class TestDateTimeJSONEncoder(TestCase):
    def test_datetime_encoding(self):
        a_naive_datetime = datetime(2012, 05, 01, 07, 27, 10, 20000)
        a_tz_datetime = datetime(2012, 05, 01, 07, 27, 10, 20000, tzinfo=UTC)
        a_date = a_naive_datetime.date()
        an_iso_datetime = '2012-05-01T07:27:10.020000+00:00'
        an_iso_date = '2012-05-01'

        obj = {
            'number': 100,
            'string': 'hello',
            'object': {'a': 1},
            'a_datetime': a_naive_datetime,
            'a_tz_datetime': a_tz_datetime,
            'a_date': a_date,
        }

        to_json = json.dumps(obj, cls=DateTimeJSONEncoder)
        from_json = json.loads(to_json)

        self.assertEqual(from_json['number'], 100)
        self.assertEqual(from_json['string'], 'hello')
        self.assertEqual(from_json['object'], {'a': 1})

        self.assertEqual(from_json['a_datetime'], an_iso_datetime)
        self.assertEqual(from_json['a_tz_datetime'], an_iso_datetime)
        self.assertEqual(from_json['a_date'], an_iso_date)
