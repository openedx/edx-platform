# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django_countries.fields import CountryField

from functools import partial

from lms.djangoapps.onboarding.models import Organization
from .helpers import upload_to_path
from .constants import CITY_MAX_LENGTH, TITLE_MAX_LENGTH, OVERVIEW_MAX_LENGTH


class Location(models.Model):
    country = CountryField()
    city = models.CharField(max_length=CITY_MAX_LENGTH)

    @property
    def location(self):
        return '{city}, {country}'.format(city=self.city, country=self.country.name)

    class Meta:
        abstract = True


class VisualAttachment(models.Model):
    video_link = models.URLField(blank=True, null=True)
    image = models.ImageField(
        upload_to=partial(upload_to_path, folder='images'), blank=True, null=True,
        validators=[FileExtensionValidator(['jpg', 'png'])],
        help_text='Accepted extensions: .jpg, .png'
    )
    file = models.FileField(
        upload_to=partial(upload_to_path, folder='files'), blank=True, null=True,
        validators=[FileExtensionValidator(['docx', 'pdf', 'txt'])],
        help_text='Accepted extensions: .docx, .pdf, .txt'
    )

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

    class Meta:
        abstract = True


class Idea(OrganizationBase, Location, VisualAttachment):
    user = models.ForeignKey(User, related_name='ideas', related_query_name='idea', on_delete=models.CASCADE)
    title = models.CharField(max_length=TITLE_MAX_LENGTH)
    overview = models.CharField(max_length=OVERVIEW_MAX_LENGTH)
    description = models.TextField()
    implementation = models.TextField(blank=True)
    favorites = models.ManyToManyField(User, related_name='favorite_ideas')

    def toggle_favorite(self, user):

        if self.favorites.filter(pk=user.id).exists():
            self.favorites.remove(user)
            return False

        self.favorites.add(user)
        return True

    def __unicode__(self):
        return self.title

    class Meta(object):
        app_label = 'idea'
