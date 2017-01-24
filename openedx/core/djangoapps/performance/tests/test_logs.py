# pylint: disable=no-member
"""
Tests that performance data is successfully logged.
"""
import datetime
import dateutil
import json

import logging
from StringIO import StringIO

from django.test import TestCase
from django.test.client import RequestFactory
from openedx.core.djangoapps.performance.views import performance_log


class PerformanceTrackingTest(TestCase):
    """
    Tests that performance logs correctly handle events
    """

    def setUp(self):
        super(PerformanceTrackingTest, self).setUp()
        self.request_factory = RequestFactory()
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.log = logging.getLogger()
        self.log.setLevel(logging.INFO)
        for handler in self.log.handlers:
            self.log.removeHandler(handler)
        self.log.addHandler(self.handler)
        self.addCleanup(self.log.removeHandler, self.handler)
        self.addCleanup(self.handler.close)

    def test_empty_get(self):
        request = self.request_factory.get('/performance')
        pre_time = datetime.datetime.utcnow()
        performance_log(request)
        post_time = datetime.datetime.utcnow()
        self.handler.flush()
        logged_value = json.loads(self.stream.getvalue().strip())
        self.assertEqual(logged_value['accept_language'], '')
        self.assertEqual(logged_value['agent'], '')
        self.assertEqual(logged_value['event'], '')
        self.assertEqual(logged_value['event_source'], 'browser')
        self.assertEqual(logged_value['expgroup'], '')
        self.assertEqual(logged_value['id'], '')
        self.assertEqual(logged_value['page'], '')
        self.assertEqual(logged_value['referer'], '')
        self.assertEqual(logged_value['value'], '')
        logged_time = dateutil.parser.parse(logged_value['time']).replace(tzinfo=None)
        self.assertLessEqual(pre_time, logged_time)
        self.assertGreaterEqual(post_time, logged_time)

    def test_empty_post(self):
        request = self.request_factory.post('/performance')
        pre_time = datetime.datetime.utcnow()
        performance_log(request)
        post_time = datetime.datetime.utcnow()
        self.handler.flush()
        logged_value = json.loads(self.stream.getvalue().strip())
        self.assertEqual(logged_value['accept_language'], '')
        self.assertEqual(logged_value['agent'], '')
        self.assertEqual(logged_value['event'], '')
        self.assertEqual(logged_value['event_source'], 'browser')
        self.assertEqual(logged_value['expgroup'], '')
        self.assertEqual(logged_value['id'], '')
        self.assertEqual(logged_value['page'], '')
        self.assertEqual(logged_value['referer'], '')
        self.assertEqual(logged_value['value'], '')
        logged_time = dateutil.parser.parse(logged_value['time']).replace(tzinfo=None)
        self.assertLessEqual(pre_time, logged_time)
        self.assertGreaterEqual(post_time, logged_time)

    def test_populated_get(self):
        request = self.request_factory.get('/performance',
                                           {'event': "a_great_event",
                                            'id': "12345012345",
                                            'expgroup': "17", 'page': "atestpage",
                                            'value': "100234"})
        request.META['HTTP_ACCEPT_LANGUAGE'] = "en"
        request.META['HTTP_REFERER'] = "https://www.edx.org/evilpage"
        request.META['HTTP_USER_AGENT'] = "Mozilla/5.0"
        request.META['REMOTE_ADDR'] = "18.19.20.21"
        request.META['SERVER_NAME'] = "some-aws-server"
        pre_time = datetime.datetime.utcnow()
        performance_log(request)
        post_time = datetime.datetime.utcnow()
        self.handler.flush()
        logged_value = json.loads(self.stream.getvalue().strip())
        self.assertEqual(logged_value['accept_language'], 'en')
        self.assertEqual(logged_value['agent'], 'Mozilla/5.0')
        self.assertEqual(logged_value['event'], 'a_great_event')
        self.assertEqual(logged_value['event_source'], 'browser')
        self.assertEqual(logged_value['expgroup'], '17')
        self.assertEqual(logged_value['host'], 'some-aws-server')
        self.assertEqual(logged_value['id'], '12345012345')
        self.assertEqual(logged_value['ip'], '18.19.20.21')
        self.assertEqual(logged_value['page'], 'atestpage')
        self.assertEqual(logged_value['referer'], 'https://www.edx.org/evilpage')
        self.assertEqual(logged_value['value'], '100234')
        logged_time = dateutil.parser.parse(logged_value['time']).replace(tzinfo=None)
        self.assertLessEqual(pre_time, logged_time)
        self.assertGreaterEqual(post_time, logged_time)

    def test_populated_post(self):
        request = self.request_factory.post('/performance',
                                            {'event': "a_great_event",
                                             'id': "12345012345",
                                             'expgroup': "17", 'page': "atestpage",
                                             'value': "100234"})
        request.META['HTTP_ACCEPT_LANGUAGE'] = "en"
        request.META['HTTP_REFERER'] = "https://www.edx.org/evilpage"
        request.META['HTTP_USER_AGENT'] = "Mozilla/5.0"
        request.META['REMOTE_ADDR'] = "18.19.20.21"
        request.META['SERVER_NAME'] = "some-aws-server"
        pre_time = datetime.datetime.utcnow()
        performance_log(request)
        post_time = datetime.datetime.utcnow()
        self.handler.flush()
        logged_value = json.loads(self.stream.getvalue().strip())
        self.assertEqual(logged_value['accept_language'], 'en')
        self.assertEqual(logged_value['agent'], 'Mozilla/5.0')
        self.assertEqual(logged_value['event'], 'a_great_event')
        self.assertEqual(logged_value['event_source'], 'browser')
        self.assertEqual(logged_value['expgroup'], '17')
        self.assertEqual(logged_value['host'], 'some-aws-server')
        self.assertEqual(logged_value['id'], '12345012345')
        self.assertEqual(logged_value['ip'], '18.19.20.21')
        self.assertEqual(logged_value['page'], 'atestpage')
        self.assertEqual(logged_value['referer'], 'https://www.edx.org/evilpage')
        self.assertEqual(logged_value['value'], '100234')
        logged_time = dateutil.parser.parse(logged_value['time']).replace(tzinfo=None)
        self.assertLessEqual(pre_time, logged_time)
        self.assertGreaterEqual(post_time, logged_time)
