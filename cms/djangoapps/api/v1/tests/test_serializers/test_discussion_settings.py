""" Tests for discussion settings api serializer and helper functions """


from datetime import datetime

import ddt
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import serializers

from cms.djangoapps.api.v1.serializers.discussion_settings import blackout_date_range_validator, to_datetime
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@ddt.ddt
class DiscussionSettingsSerializerTests(ModuleStoreTestCase):
    """
    Test cases for discussion settings serializer validation & helpers
    """

    def test_to_datetime_helper(self):
        success_data = [
            (("2015-09-11", datetime.min.time()), datetime.combine(parse_date("2015-09-11"), datetime.min.time())),
            (("2015-09-11T02:45", None), parse_datetime("2015-09-11T02:45")),
        ]
        for args, expected in success_data:
            assert expected == to_datetime(*args)

        with self.assertRaises(ValueError):
            to_datetime("Invalid Date", None)

    def test_blackout_date_range_validator(self):
        date_range = ["2015-09-11", "2015-09-14"]
        result = blackout_date_range_validator(date_range)
        self.assertEqual(result, date_range)

        date_range = ["2015-09-11T02:45", "2015-09-14T04:45"]
        result = blackout_date_range_validator(date_range)
        self.assertEqual(result, date_range)

        with self.assertRaises(serializers.ValidationError):
            date_range = ["2015-09-14", "2015-09-11"]
            blackout_date_range_validator(date_range)
