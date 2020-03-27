from django.db import models

from django_countries.fields import CountryField
from model_utils.models import TimeStampedModel

from .constants import JOB_COMPENSATION_CHOICES, JOB_HOURS_CHOICES, JOB_TYPE_CHOICES


class Job(TimeStampedModel):
    """
    This model contains all the fields related to a job being
    posted on the job board.
    """
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    type = models.CharField(max_length=255, choices=JOB_TYPE_CHOICES)
    compensation = models.CharField(max_length=255, choices=JOB_COMPENSATION_CHOICES)
    hours = models.CharField(max_length=255, choices=JOB_HOURS_CHOICES)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = CountryField(null=True, blank=True)
    description = models.TextField()
    function = models.TextField()
    responsibilities = models.TextField()
