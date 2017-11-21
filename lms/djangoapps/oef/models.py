from django.db import models
from model_utils.models import TimeStampedModel

from student.models import User


class OefSurvey(TimeStampedModel):
    user = models.ForeignKey(User)
    is_complete = models.BooleanField(default=False)


class OptionPriority(TimeStampedModel):
    label = models.CharField(max_length=50)
    value = models.FloatField()


class Topic(TimeStampedModel):
    survey = models.ForeignKey(OefSurvey)
    is_enabled = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    selected_option = models.ForeignKey(OptionPriority, null=True, blank=True)
    title = models.TextField()
    description = models.TextField()


class Option(TimeStampedModel):
    topic = models.ForeignKey(Topic)
    priority = models.ForeignKey(OptionPriority)
    text = models.TextField()
