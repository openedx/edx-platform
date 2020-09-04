"""
Models file for classrooms application
"""
from django.contrib.auth.models import User
from django.db import models
from model_utils.models import TimeStampedModel

from nodebb.models import DiscussionCommunity


class DiscussionCommunityMembership(TimeStampedModel):
    """
    A class to associated user with community
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    community = models.ForeignKey(DiscussionCommunity, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("user", "community"),)

    def __unicode__(self):
        return u"<DiscussionCommunityMembership: {user} >".format(user=self.user)
