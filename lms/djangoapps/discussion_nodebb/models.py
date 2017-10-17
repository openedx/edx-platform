"""
    Models related to nodeBB integrations
"""
from django.db import models
from model_utils.models import TimeStampedModel
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class DiscussionCommunity(TimeStampedModel):
    """
        Model to store each course related communities
    """

    course_id = CourseKeyField(max_length=255, db_index=True)
    community_url = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return "%s %s" % (self.course.display_name, self.community_url)