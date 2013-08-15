from __future__ import absolute_import

import logging

import dateutil

from django.db import models

from track.backends.base import BaseBackend


log = logging.getLogger('track.backends.django')


LOGFIELDS = [
    'username',
    'ip',
    'event_source',
    'event_type',
    'event',
    'agent',
    'page',
    'time',
    'host'
]


class TrackingLog(models.Model):
    """Defines the fields that are stored in the tracking log database"""

    dtcreated = models.DateTimeField('creation date', auto_now_add=True)
    username = models.CharField(max_length=32, blank=True)
    ip = models.CharField(max_length=32, blank=True)
    event_source = models.CharField(max_length=32)
    event_type = models.CharField(max_length=512, blank=True)
    event = models.TextField(blank=True)
    agent = models.CharField(max_length=256, blank=True)
    page = models.CharField(max_length=512, blank=True, null=True)
    time = models.DateTimeField('event time')
    host = models.CharField(max_length=64, blank=True)

    def __unicode__(self):
        fmt = (
            u"[{self.time}] {self.username}@{self.ip}: "
            u"{self.event_source}| {self.event_type} | "
            u"{self.page} | {self.event}"
        )
        return fmt.format(self=self)


class DjangoBackend(BaseBackend):
    def __init__(self, **options):
        super(DjangoBackend, self).__init__(**options)

    def send(self, event):
        event['time'] = dateutil.parser.parse(event['time'])
        tldat = TrackingLog(**dict((x, event[x]) for x in LOGFIELDS))
        try:
            tldat.save()
        except Exception as e:
            log.exception(e)
