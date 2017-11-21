from django.db import models
# Create your models here.
from model_utils.models import TimeStampedModel

from student.models import User


class OefSurvey(TimeStampedModel):
    user = models.ForeignKey(User)
    is_complete = models.BooleanField(default=False)


class Topic(TimeStampedModel):
    survey = models.ForeignKey(OefSurvey)
    is_enabled = models.BooleanField(default=True)
    title = models.TextField()
    description = models.TextField()


class Options(TimeStampedModel):
    topic = models.ForeignKey(Topic)
    priority = models.IntegerField()
    text = models.TextField()
