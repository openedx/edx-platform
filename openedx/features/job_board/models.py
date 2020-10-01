"""
Models for Job Board
"""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from model_utils.models import TimeStampedModel

from util.philu_utils import UploadToPathAndRename

from .constants import (
    JOB_COMPENSATION_CHOICES,
    JOB_HOURS_CHOICES,
    JOB_TYPE_CHOICES,
    LOGO_ALLOWED_EXTENSION,
    LOGO_IMAGE_MAX_SIZE
)
from .helpers import validate_file_size


class Job(TimeStampedModel):
    """
    This model contains all the fields related to a job being
    posted on the job board.
    """

    title = models.CharField(max_length=255, verbose_name=_('Job Title'))
    company = models.CharField(max_length=255, verbose_name=_('Organization Name'))
    type = models.CharField(
        max_length=255,
        choices=JOB_TYPE_CHOICES, verbose_name=_('Job Type'),
        help_text=_('Please select whether the job is onsite or can be done remotely.'),
        default='remote'
    )
    compensation = models.CharField(
        max_length=255,
        choices=JOB_COMPENSATION_CHOICES,
        verbose_name=_('Compensation'),
        help_text=_('Please select the type of compensation you are offering for this job.'),
        default='volunteer'
    )
    hours = models.CharField(
        max_length=255,
        choices=JOB_HOURS_CHOICES,
        verbose_name=_('Job Hours'),
        help_text=_('Please select the expected number of working hours required for this job.'),
        default='fulltime'
    )
    city = models.CharField(max_length=255, verbose_name=_('City'))
    country = CountryField(verbose_name=_('Country'))
    description = models.TextField(
        verbose_name=_('Job Description'), help_text=_('Please share a brief description of the job.')
    )
    function = models.TextField(
        verbose_name=_('Job Function'),
        help_text=_('Please share details about the expected functions associated with the job.')
    )
    responsibilities = models.TextField(
        verbose_name=_('Job Responsibilities'),
        help_text=_('Please share the responsibilities associated with the job.')
    )
    website_link = models.URLField(max_length=255, blank=True, null=True, verbose_name=_('Website Link'))
    application_link = models.URLField(max_length=255, blank=True, null=True, verbose_name=_('Application Link'))
    contact_email = models.EmailField(max_length=255, verbose_name=_('Contact Email'))
    logo = models.ImageField(
        upload_to=UploadToPathAndRename('job-board/uploaded-logos/', 'image'),
        blank=True,
        null=True,
        verbose_name=_('Company Logo'),
        max_length=500,
        validators=[FileExtensionValidator(LOGO_ALLOWED_EXTENSION), validate_file_size],
        help_text=format_lazy(
            _("Please upload a file with your company's logo. (maximum {image_size}MB)"),
            image_size=LOGO_IMAGE_MAX_SIZE / 1024 / 1024
        )
    )

    @property
    def location(self):
        """Get the full location (city, country) of job."""
        return '{city}, {country}'.format(city=self.city, country=self.country.name)

    def __unicode__(self):
        return self.title
