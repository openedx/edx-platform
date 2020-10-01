# -*- coding: utf-8 -*-
"""
Models for Idea app
"""
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from model_utils.models import TimeStampedModel

from lms.djangoapps.onboarding.models import Organization
from openedx.features.philu_utils.backend_storage import CustomS3Storage
from openedx.features.philu_utils.utils import bytes_to_mb
from util.philu_utils import UploadToPathAndRename

from .constants import CITY_MAX_LENGTH, IDEA_FILE_MAX_SIZE, IDEA_IMAGE_MAX_SIZE, OVERVIEW_MAX_LENGTH, TITLE_MAX_LENGTH


class Location(models.Model):
    """
    Model contains fields related to location
    """
    country = CountryField()
    city = models.CharField(max_length=CITY_MAX_LENGTH)

    @property
    def location(self):
        return '{city}, {country}'.format(city=self.city, country=self.country.name)

    class Meta:
        abstract = True


class VisualAttachment(models.Model):
    """
    Model contains fields related to visual attachment
    """
    video_link = models.URLField(blank=True, null=True, verbose_name=_('VIDEO LINK'))
    image = models.ImageField(
        storage=CustomS3Storage(), max_length=500, blank=True, null=True,
        upload_to=UploadToPathAndRename(path='images', name_prefix='image', add_path_prefix=True),
        validators=[FileExtensionValidator(['jpg', 'png'], )], verbose_name=_('ADD IMAGE'),
        help_text=format_lazy(
            _('Accepted extensions: .jpg, .png (maximum {mb} MB)'), mb=bytes_to_mb(IDEA_IMAGE_MAX_SIZE)
        )
    )
    file = models.FileField(
        storage=CustomS3Storage(), max_length=500, blank=True, null=True,
        upload_to=UploadToPathAndRename(path='files', add_path_prefix=True),
        validators=[FileExtensionValidator(['docx', 'pdf', 'txt'])],
        verbose_name=_('ADD FILE'),
        help_text=format_lazy(
            _('Accepted extensions: .docx, .pdf, .txt (maximum {mb} MB)'), mb=bytes_to_mb(IDEA_FILE_MAX_SIZE)
        )
    )

    class Meta:
        abstract = True


class OrganizationBase(models.Model):
    """
    Model contains fields related to organization and its mission
    """
    organization = models.ForeignKey(
        Organization,
        related_name='%(app_label)s_%(class)ss',
        related_query_name='%(app_label)s_%(class)s',
        on_delete=models.CASCADE
    )
    organization_mission = models.TextField(verbose_name=_('Organization Mission'))

    class Meta:
        abstract = True


class Idea(OrganizationBase, Location, VisualAttachment, TimeStampedModel):
    """
    Model contains all the fields related to Idea
    """
    user = models.ForeignKey(User, related_name='ideas', related_query_name='idea', on_delete=models.CASCADE)
    title = models.CharField(max_length=TITLE_MAX_LENGTH, verbose_name=_('Idea Title'))
    overview = models.CharField(max_length=OVERVIEW_MAX_LENGTH, verbose_name=_('Idea Overview'))
    description = models.TextField(verbose_name=_('Idea Description'))
    implementation = models.TextField(blank=True, verbose_name=_('Have you tried to implement this idea?'))
    favorites = models.ManyToManyField(User, related_name='favorite_ideas')

    class Meta(object):
        app_label = 'idea'

    def __unicode__(self):
        return self.title

    def toggle_favorite(self, user):
        """
        Toggle favorite status of idea.

        Arguments:
            user (User): Django User object

        Returns:
            bool: boolean value regarding favorite status
        """
        if self.favorites.filter(pk=user.id).exists():
            self.favorites.remove(user)  # pylint: disable=no-member
            return False

        self.favorites.add(user)  # pylint: disable=no-member
        return True

    def get_absolute_url(self):
        return reverse('idea-create')
