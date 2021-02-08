from django.db import models
from model_utils.models import TimeStampedModel

from lms.djangoapps.onboarding.models import Organization
from student.models import User


class OefSurvey(TimeStampedModel):
    class Meta:
        app_label = 'oef'

    title = models.CharField(max_length=256)
    is_enabled = models.BooleanField(default=False)
    description = models.TextField()

    def __str__(self):
        return self.title


class OptionLevel(TimeStampedModel):
    class Meta:
        app_label = 'oef'

    label = models.CharField(max_length=50)
    value = models.FloatField()
    caption = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.label


class TopicQuestion(TimeStampedModel):
    class Meta:
        app_label = 'oef'

    survey = models.ForeignKey(OefSurvey, related_name='topics')
    title = models.TextField()
    score_name = models.CharField(max_length=50)
    description = models.TextField()
    order_number = models.IntegerField()

    def __str__(self):
        return self.title


class Option(TimeStampedModel):
    class Meta:
        app_label = 'oef'

    topic = models.ForeignKey(TopicQuestion, related_name='options')
    level = models.ForeignKey(OptionLevel)
    text = models.TextField()
    short_text = models.TextField()

    def __str__(self):
        return self.text[:20]


class OrganizationOefScore(TimeStampedModel):
    class Meta:
        app_label = 'oef'

    org = models.ForeignKey(Organization, related_name="organization_oef_scores")
    user = models.ForeignKey(User, related_name="organization_oef_scores")
    start_date = models.DateField()
    finish_date = models.DateField(null=True, blank=True)
    version = models.CharField(max_length=10, default="v1.0")
    human_resource_score = models.PositiveIntegerField(null=True, blank=True)
    leadership_score = models.PositiveIntegerField(null=True, blank=True)
    financial_management_score = models.PositiveIntegerField(null=True, blank=True)
    fundraising_score = models.PositiveIntegerField(null=True, blank=True)
    measurement_score = models.PositiveIntegerField(null=True, blank=True)
    marketing_score = models.PositiveIntegerField(null=True, blank=True)
    strategy_score = models.PositiveIntegerField(null=True, blank=True)
    program_design_score = models.PositiveIntegerField(null=True, blank=True)
    external_relations_score = models.PositiveIntegerField(null=True, blank=True)
    systems_score = models.PositiveIntegerField(null=True, blank=True)


class OrganizationOefUpdatePrompt(models.Model):
    class Meta:
        app_label = 'oef'

    org = models.ForeignKey(Organization, related_name="organization_oef_update_prompts")
    responsible_user = models.ForeignKey(User, related_name="organization_oef_update_prompts")
    latest_finish_date = models.DateTimeField()
    year = models.BooleanField(default=False)


class Instruction(TimeStampedModel):
    class Meta:
        app_label = 'oef'

    question_index = models.IntegerField()
    question = models.TextField()
    answer = models.TextField()
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return str(self.question_index)
