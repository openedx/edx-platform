# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.validators import FileExtensionValidator
from django.db import models
from django_countries.fields import CountryField
from model_utils.models import TimeStampedModel

from .constants import JOB_COMPENSATION_CHOICES, JOB_HOURS_CHOICES, JOB_TYPE_CHOICES, LOGO_ALLOWED_EXTENSION, \
    LOGO_IMAGE_MAX_SIZE
from .helpers import validate_file_size


class Job(TimeStampedModel):
    """
    This model contains all the fields related to a job being
    posted on the job board.
    """
    title = models.CharField(max_length=255, verbose_name='Job Title')
    company = models.CharField(max_length=255, verbose_name='Organization Name')
    type = models.CharField(max_length=255, choices=JOB_TYPE_CHOICES, verbose_name='Job Type',
                            help_text='Please select whether the job is onsite or can be done remotely.',
                            blank=False, default=0)
    compensation = models.CharField(max_length=255, choices=JOB_COMPENSATION_CHOICES, verbose_name='Compensation',
                                    help_text='Please select the type of compensation you are offering for this job.',
                                    blank=False, default=0)
    hours = models.CharField(max_length=255, choices=JOB_HOURS_CHOICES, verbose_name='Job Hours',
                             help_text='Please select the expected number of working hours required for this job.',
                             blank=False, default=0)
    city = models.CharField(max_length=255, verbose_name='City')
    country = CountryField(verbose_name='Country')
    description = models.TextField(verbose_name='Job Description',
                                   help_text='Please share a brief description of the job.')
    function = models.TextField(blank=True, null=True, verbose_name='Job Function',
                                help_text='Please share details about the expected functions associated with the job.')
    responsibilities = models.TextField(blank=True, null=True, verbose_name='Job Responsibilities',
                                        help_text='Please share the responsibilities associated with the job.')
    website_link = models.URLField(max_length=255, blank=True, null=True, verbose_name='Website Link')
    application_link = models.URLField(max_length=255, blank=True, null=True, verbose_name='Application Link',
                                       help_text='Please share a link to the job application')
    contact_email = models.EmailField(max_length=255, verbose_name='Contact Email',
                                      help_text='Please share a contact email for this job.')
    logo = models.ImageField(upload_to='job-board/uploaded-logos/', blank=True, null=True, verbose_name='Company Logo',
                             validators=[
                                 FileExtensionValidator(LOGO_ALLOWED_EXTENSION), validate_file_size
                             ],
                             help_text='Please upload a file with your company\'s logo. (maximum {} MB)'.format(LOGO_IMAGE_MAX_SIZE))

    @property
    def location(self):
        """Get the full location (city, country) of job."""
        return '{city}, {country}'.format(city=self.city, country=self.country.name)
