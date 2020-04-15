# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
    city = models.CharField(max_length=255)
    country = CountryField()
    description = models.TextField()
    function = models.TextField(blank=True, null=True)
    responsibilities = models.TextField(blank=True, null=True)
    website_link = models.URLField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(max_length=255)
    logo = models.ImageField(upload_to='job-board/uploaded-logos/', blank=True, null=True)

    @property
    def location(self):
        """Get the full location (city, country) of job."""
        return '{city}, {country}'.format(city=self.city, country=self.country.name)
