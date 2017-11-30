from django.db import models
from model_utils.models import TimeStampedModel

from student.models import User


class OefSurvey(TimeStampedModel):
    title = models.CharField(max_length=256)
    is_enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class OptionLevel(TimeStampedModel):
    label = models.CharField(max_length=50)
    value = models.FloatField()
    caption = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.label


class TopicQuestion(TimeStampedModel):
    survey = models.ForeignKey(OefSurvey, related_name='topics')
    title = models.TextField()
    description = models.TextField()

    def __str__(self):
        return self.title


class Option(TimeStampedModel):
    topic = models.ForeignKey(TopicQuestion, related_name='options')
    level = models.ForeignKey(OptionLevel)
    text = models.TextField()

    def __str__(self):
        return self.text[:20]


class UserOefSurvey(TimeStampedModel):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    )
    user = models.ForeignKey(User)
    survey = models.ForeignKey(OefSurvey)
    started_on = models.DateField()
    completed_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return '-'.join([self.user.username, self.survey.title])


class UserAnswers(TimeStampedModel):
    user_survey = models.ForeignKey(UserOefSurvey, related_name='answers')
    question = models.ForeignKey(TopicQuestion)
    selected_option = models.ForeignKey(OptionLevel)
