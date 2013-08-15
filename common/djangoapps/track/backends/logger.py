from __future__ import absolute_import

import logging
import json

from django.conf import settings

from track.backends.base import BaseBackend


log = logging.getLogger('track.backends.logger')


class LoggerBackend(BaseBackend):
    def __init__(self, **options):
        super(LoggerBackend, self).__init__(**options)
        self.output = logging.getLogger('tracking')

    def send(self, event):
        event_str = json.dumps(event)
        self.output.info(event_str[:settings.TRACK_MAX_EVENT])
