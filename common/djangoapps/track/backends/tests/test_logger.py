from __future__ import absolute_import

import json
import logging

from django.test import TestCase

from track.backends.logger import LoggerBackend


class TestLoggerBackend(TestCase):
    def setUp(self):

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

        event = {'test': True}
        event_as_json = json.dumps(event)

        self.backend.send(event)
        self.backend.send(event)

        self.assertEqual(
            self.handler.messages['info'],
            [event_as_json, event_as_json]
        )


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
