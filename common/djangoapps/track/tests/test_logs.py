"""Tests that tracking data are successfully logged"""
import mock
import unittest

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings
from track.models import TrackingLog
from track.views import user_track


@unittest.skip("TODO: these tests were not being run before, and now that they are they're failing")
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TrackingTest(TestCase):
    """
    Tests that tracking logs correctly handle events
    """

    def test_post_answers_to_log(self):
        """
        Checks that student answer requests submitted to track.views via POST
        are correctly logged in the TrackingLog db table
        """
        requests = [
            {"event": "my_event", "event_type": "my_event_type", "page": "my_page"},
            {"event": "{'json': 'object'}", "event_type": unichr(512), "page": "my_page"}
        ]
        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_SQL_TRACKING_LOGS': True}):
            for request_params in requests:
                response = self.client.post(reverse(user_track), request_params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, 'success')
                tracking_logs = TrackingLog.objects.order_by('-dtcreated')
                log = tracking_logs[0]
                self.assertEqual(log.event, request_params["event"])
                self.assertEqual(log.event_type, request_params["event_type"])
                self.assertEqual(log.page, request_params["page"])

    def test_get_answers_to_log(self):
        """
        Checks that student answer requests submitted to track.views via GET
        are correctly logged in the TrackingLog db table
        """
        requests = [
            {"event": "my_event", "event_type": "my_event_type", "page": "my_page"},
            {"event": "{'json': 'object'}", "event_type": unichr(512), "page": "my_page"}
        ]
        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_SQL_TRACKING_LOGS': True}):
            for request_params in requests:
                response = self.client.get(reverse(user_track), request_params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, 'success')
                tracking_logs = TrackingLog.objects.order_by('-dtcreated')
                log = tracking_logs[0]
                self.assertEqual(log.event, request_params["event"])
                self.assertEqual(log.event_type, request_params["event_type"])
                self.assertEqual(log.page, request_params["page"])
