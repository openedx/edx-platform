from __future__ import absolute_import

import logging
import json

from django.conf import settings

from track.backends.base import BaseBackend

log = logging.getLogger('track.backends.logger')


class LoggerBackend(BaseBackend):
    def __init__(self, **options):
        super(LoggerBackend, self).__init__(**options)

        # TODO: the configuration of the logger backend should come
        # from the constructor options. Currently is being done using
        # the Django settings for a logger named 'tracking'.

        self.output_log = logging.getLogger('tracking')

    def send(self, event):
        event_str = json.dumps(event)

        # TODO: remove trucation of the serialized event, either at a
        # higher level during the emittion of the event, or by
        # providing warnings when the events exceed certain size.
        event_str = event_str[:settings.TRACK_MAX_EVENT]

        self.output_log.info(event_str)
