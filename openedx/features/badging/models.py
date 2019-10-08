from django.db import models

from .constants import CONVERSATIONALIST, TEAM_PLAYER


class Badge(models.Model):
    BADGE_TYPES = (
        CONVERSATIONALIST,
        TEAM_PLAYER
    )

    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    threshold = models.IntegerField(blank=False, null=False)
    type = models.CharField(max_length=100, blank=False, null=False, choices=BADGE_TYPES)
    image = models.CharField(max_length=255, blank=False, null=False)
    date_created = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name
