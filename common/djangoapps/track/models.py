from django.db import models

from django.db import models


class TrackingLog(models.Model):
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
        s = "[%s] %s@%s: %s | %s | %s | %s" % (self.time, self.username, self.ip, self.event_source,
                                               self.event_type, self.page, self.event)
        return s
