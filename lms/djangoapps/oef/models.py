from django.db import models
from model_utils.models import TimeStampedModel

from lms.djangoapps.onboarding.models import Organization
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
    short_text = models.TextField()

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


class OrganizationOefScore(TimeStampedModel):
    org = models.ForeignKey(Organization, related_name="organization_oef_scores")
    user = models.ForeignKey(User, related_name="organization_oef_scores")
    start_date = models.DateField()
    finish_date = models.DateField()
    version = models.CharField(max_length=10, default="v1.0")
    human_resource_score = models.PositiveIntegerField()
    leadership_score = models.PositiveIntegerField()
    financial_management_score = models.PositiveIntegerField()
    fundraising_score = models.PositiveIntegerField()
    measurement_score = models.PositiveIntegerField()
    marketing_score = models.PositiveIntegerField()
    strategy_score = models.PositiveIntegerField()
    program_design_score = models.PositiveIntegerField()
    external_relations_score = models.PositiveIntegerField()
    systems_score = models.PositiveIntegerField()
