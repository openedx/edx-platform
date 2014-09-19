"""
Tests displaying course start time in CMS
"""
import unittest
from datetime import datetime, timedelta
import xmodule.course_module
from mock import Mock, patch
from django.utils.timezone import UTC
from xmodule.tests.test_course_module import get_dummy_course

NOW = datetime.strptime('2013-01-01T01:00:00', '%Y-%m-%dT%H:%M:00').replace(tzinfo=UTC())


class CMSCourseStartTimeTests(unittest.TestCase):
    """ Test that course start time is returned correctly """
    start_times = [
        # start time, expected return in UTC
        ('2012-12-02T12:00', 'Dec 02, 2012'),
        ('2014-01-01T3:00', 'Jan 01, 2014'),
        ('2014-07-31T3:00', 'Jul 31, 2014'),
        ('2014-07-31T18:00', 'Jul 31, 2014'),
    ]

    def test_cms_start_date(self):
        """ Test start date text in cms, should just convert to date format"""
        for times in self.start_times:
            course = get_dummy_course(start=times[0])
            self.assertEqual(course.start_date_text, times[1])
