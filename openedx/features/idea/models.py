# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django_countries.fields import CountryField

from functools import partial

from lms.djangoapps.onboarding.models import Organization
from .helpers import upload_to_path


class Location(models.Model):
    country = CountryField()
    city = models.CharField(max_length=255)

    @property
    def location(self):
        return '{city}, {country}'.format(city=self.city, country=self.country)

    def __unicode__(self):
        return self.location

    class Meta:
        abstract = True


class VisualAttachment(models.Model):

    video_link = models.URLField(blank=True, null=True)
    image = models.FileField(
        upload_to=partial(upload_to_path, folder='images'), blank=True, null=True,
        validators=[FileExtensionValidator(['jpg', 'png', 'pdf'])],
        help_text='Accepted extensions: .jpg, .png, .pdf'
    )
    file = models.FileField(
        upload_to=partial(upload_to_path, folder='files'), blank=True, null=True,
        validators=[FileExtensionValidator(['docx', 'pdf', 'txt'])],
        help_text='Accepted extensions: .docx, .pdf, .txt'
    )

    def __unicode__(self):
        return self.video_link

    class Meta:
        abstract = True


class OrganizationBase(models.Model):
    organization = models.ForeignKey(
        Organization,
        related_name='%(app_label)s_%(class)ss',
        related_query_name='%(app_label)s_%(class)s',
        on_delete=models.CASCADE
    )
    organization_mission = models.TextField()

    def __unicode__(self):
        return self.organization.label

    class Meta:
        abstract = True


class Idea(OrganizationBase, Location, VisualAttachment):
    user = models.ForeignKey(User, related_name='ideas', related_query_name='idea', on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    overview = models.CharField(max_length=150)
    description = models.TextField()
    implementation = models.TextField(blank=True)

    def __unicode__(self):
        return self.title

    class Meta(object):
        app_label = 'idea'
