"""
All models for webinars app
"""
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from openedx.adg.lms.applications.helpers import validate_file_size

from .constants import ALLOWED_BANNER_EXTENSIONS, BANNER_MAX_SIZE


class Webinar(TimeStampedModel):
    """
    Model to create a webinar
    """

    start_time = models.DateTimeField(verbose_name=_('Start Time'), )
    end_time = models.DateTimeField(verbose_name=_('End Time'), )

    title = models.CharField(verbose_name=_('Title'), max_length=255, )
    description = models.TextField(verbose_name=_('Description'), )
    presenter = models.ForeignKey(
        User, verbose_name=_('Presenter'), on_delete=models.CASCADE, related_name='webinar_presenter',
    )
    meeting_link = models.URLField(default='', verbose_name=_('Meeting Link'), blank=True, )
    banner = models.ImageField(
        upload_to='webinar/banners/',
        verbose_name=_('Banner'),
        validators=[FileExtensionValidator(ALLOWED_BANNER_EXTENSIONS)],
        help_text=_('Accepted extensions: .png, .jpg, .jpeg, .svg'),
    )

    language = models.CharField(verbose_name=_('Language'), choices=settings.LANGUAGES, max_length=2,)

    co_hosts = models.ManyToManyField(User, verbose_name=_('Co-Hosts'), blank=True, related_name='webinar_co_hosts', )
    panelists = models.ManyToManyField(
        User, verbose_name=_('Panelists'), blank=True, related_name='webinar_panelists',
    )

    UPCOMING = 'upcoming'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = (
        (UPCOMING, _('Upcoming')),
        (DELIVERED, _('Delivered')),
        (CANCELLED, _('Cancelled'))
    )
    status = models.CharField(
        verbose_name=_('Webinar Status'), choices=STATUS_CHOICES, max_length=10, default=UPCOMING,
    )

    is_virtual = models.BooleanField(default=True, verbose_name=_('Virtual Event'), )
    created_by = models.ForeignKey(
        User, verbose_name=_('Created By'), on_delete=models.CASCADE, blank=True, related_name='webinar_created_by',
    )
    modified_by = models.ForeignKey(
        User,
        verbose_name=_('Last Modified By'),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='webinar_modified_by',
    )

    class Meta:
        app_label = 'webinars'

    def __str__(self):
        return self.title

    def clean(self):
        """
        Adding custom validation on start & end time and banner size
        """
        super().clean()

        if self.start_time and self.start_time < datetime.now():
            raise ValidationError({'start_time': _('Start date should be in future')})

        if self.end_time and self.end_time < datetime.now():
            raise ValidationError({'end_time': _('End date should be in future')})

        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValidationError({'start_time': _('End date must be greater than start date')})

        if self.banner:
            error = validate_file_size(self.banner, BANNER_MAX_SIZE)
            if error:
                raise ValidationError({'banner': error})


class WebinarRegistration(TimeStampedModel):
    """
    Model to store the user registered in webinar
    """

    webinar = models.ForeignKey(
        Webinar, verbose_name=_('Webinar'), on_delete=models.CASCADE, related_name='registrations',
    )
    user = models.ForeignKey(
        User, verbose_name=_('Registered User'), on_delete=models.CASCADE, related_name='webinar_registrations',
    )
    is_registered = models.BooleanField(verbose_name=_('Registered'), )

    class Meta:
        app_label = 'webinars'

    def __str__(self):
        return f'User {self.user}, webinar {self.webinar}'
