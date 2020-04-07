# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField

from lms.djangoapps.onboarding.models import Organization


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
    video_link = models.URLField(null=True, blank=True)
    image = models.ImageField(upload_to='idea/images/', blank=True, null=True)
    file = models.FileField(upload_to='idea/files/', null=True, blank=True)

    def __unicode__(self):
        return self.video_link

    class Meta:
        abstract = True


class OrganizationBase(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    organization_mission = models.TextField()
    contact_email = models.CharField(max_length=255)

    def __unicode__(self):
        return self.organization_name

    class Meta:
        abstract = True


class Idea(OrganizationBase, Location, VisualAttachment):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    overview = models.CharField(max_length=150)
    description = models.TextField()

    consent_to_share_idea_and_email = models.BooleanField()

    def __unicode__(self):
        return self.title
