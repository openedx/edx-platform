# -*- coding: utf-8 -*-
"""Tests for Event tracker backend."""


import datetime
import json
import logging

from common.djangoapps.track.backends.logger import LoggerBackend


def test_logger_backend(caplog):
    """
    Send a couple of events and check if they were recorded
    by the logger. The events are serialized to JSON.
    """
    caplog.set_level(logging.INFO)
    logger_name = 'common.djangoapps.track.backends.logger.test'
    backend = LoggerBackend(name=logger_name)
    event = {
        'test': True,
        'time': datetime.datetime(2012, 5, 1, 7, 27, 1, 200),
        'date': datetime.date(2012, 5, 7),
    }

    backend.send(event)
    backend.send(event)

    saved_events = [json.loads(e[2]) for e in caplog.record_tuples if e[0] == logger_name]

    unpacked_event = {
        'test': True,
        'time': '2012-05-01T07:27:01.000200+00:00',
        'date': '2012-05-07'
    }

    assert saved_events[0] == unpacked_event
    assert saved_events[1] == unpacked_event
