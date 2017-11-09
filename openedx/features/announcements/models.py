"""
Models for Announcements
"""

from django.db import models


class Announcement(models.Model):
    """Site-wide announcements to be displayed on the dashboard"""
    class Meta(object):
        app_label = 'announcements'

    content = models.CharField(max_length=1000, null=False, default="lorem ipsum")
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.content
