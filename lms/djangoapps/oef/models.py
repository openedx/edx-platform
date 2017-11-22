from django.db import models
from model_utils.models import TimeStampedModel

from student.models import User


class OefSurvey(TimeStampedModel):
    title = models.CharField(max_length=256)
    is_enabled = models.BooleanField(default=False)


class OptionPriority(TimeStampedModel):
    label = models.CharField(max_length=50)
    value = models.FloatField()


class TopicQuestion(TimeStampedModel):
    survey = models.ForeignKey(OefSurvey)
    title = models.TextField()
    description = models.TextField()


class Option(TimeStampedModel):
    topic = models.ForeignKey(TopicQuestion)
    priority = models.ForeignKey(OptionPriority)
    text = models.TextField()


class UserOefSurvey(TimeStampedModel):
    user = models.ForeignKey(User)
    survey_date = models.DateField()
    oef_survey = models.ForeignKey(OefSurvey)


class UserAnswers(TimeStampedModel):
    user = models.ForeignKey(User)
    survey_id = models.ForeignKey(OefSurvey)
    question = models.ForeignKey(TopicQuestion)
    selected_option = models.ForeignKey(OptionPriority)
