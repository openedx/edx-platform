from django.db import models
from django_countries.fields import CountryField
from model_utils.models import TimeStampedModel

from .constants import JOB_COMPENSATION_CHOICES, JOB_HOURS_CHOICES, JOB_TYPE_CHOICES


class Job(TimeStampedModel):
    """
    This model contains all the fields related to a job being
    posted on the job board.
    """
    title = models.CharField(max_length=255, null=False, blank=False)
    company = models.CharField(max_length=255, null=False, blank=False)
    type = models.CharField(max_length=32, choices=JOB_TYPE_CHOICES, blank=False)
    compensation = models.CharField(max_length=32, choices=JOB_COMPENSATION_CHOICES, blank=False)
    hours = models.CharField(max_length=32, choices=JOB_HOURS_CHOICES, blank=False)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = CountryField(null=True, blank=True)
    description = models.TextField(null=False, blank=False)
    function = models.TextField(null=False, blank=False)
    responsibilities = models.TextField(null=False, blank=False)
