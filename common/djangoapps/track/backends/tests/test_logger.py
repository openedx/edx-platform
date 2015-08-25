from __future__ import absolute_import

import json
import logging
import datetime

from django.test import TestCase

from track.backends.logger import LoggerBackend


class TestLoggerBackend(TestCase):
    def setUp(self):
        super(TestLoggerBackend, self).setUp()
        self.handler = MockLoggingHandler()
        self.handler.setLevel(logging.INFO)

        logger_name = 'track.backends.logger.test'
        logger = logging.getLogger(logger_name)
        logger.addHandler(self.handler)

        self.backend = LoggerBackend(name=logger_name)

    def test_logger_backend(self):
        self.handler.reset()

        # Send a couple of events and check if they were recorded
        # by the logger. The events are serialized to JSON.

        event = {
            'test': True,
            'time': datetime.datetime(2012, 05, 01, 07, 27, 01, 200),
            'date': datetime.date(2012, 05, 07),
        }

        self.backend.send(event)
        self.backend.send(event)

        saved_events = [json.loads(e) for e in self.handler.messages['info']]

        unpacked_event = {
            'test': True,
            'time': '2012-05-01T07:27:01.000200+00:00',
            'date': '2012-05-07'
        }

        self.assertEqual(saved_events[0], unpacked_event)
        self.assertEqual(saved_events[1], unpacked_event)


class MockLoggingHandler(logging.Handler):
    """
    Mock logging handler.

    Stores records in a dictionry of lists by level.

    """

    def __init__(self, *args, **kwargs):
        super(MockLoggingHandler, self).__init__(*args, **kwargs)
        self.messages = None
        self.reset()

    def emit(self, record):
        level = record.levelname.lower()
        message = record.getMessage()
        self.messages[level].append(message)

    def reset(self):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }
