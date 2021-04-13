"""
All models for webinars app
"""
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from openedx.adg.lms.applications.helpers import validate_file_size

from .constants import ALLOWED_BANNER_EXTENSIONS, BANNER_MAX_SIZE
from .helpers import send_cancellation_emails_for_given_webinars


class WebinarQuerySet(models.QuerySet):
    """
    Custom QuerySet that does not allow Webinars to be deleted from the database, instead marks the status of the
    deleted Webinars as `Cancelled`
    """

    def delete(self):
        cancelled_upcoming_webinars = self.filter(
            status=Webinar.UPCOMING).select_related('presenter').prefetch_related('co_hosts', 'panelists')
        send_cancellation_emails_for_given_webinars(cancelled_upcoming_webinars)
        self.update(status=Webinar.CANCELLED)


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

    objects = WebinarQuerySet.as_manager()

    class Meta:
        app_label = 'webinars'

    def __str__(self):
        return self.title

    def clean(self):
        """
        Adding custom validation on start & end time and banner size
        """
        super().clean()

        errors = {}
        if self.start_time and self.start_time < now():
            errors['start_time'] = _('Start date should be in future')

        if self.end_time and self.end_time < now():
            errors['end_time'] = _('End date should be in future')

        if self.start_time and self.end_time and self.start_time > self.end_time:
            errors['start_time'] = _('End date must be greater than start date')

        if self.banner:
            error_message = validate_file_size(self.banner, BANNER_MAX_SIZE)
            if error_message:
                errors['banner'] = error_message

        if errors:
            raise ValidationError(errors)

    def delete(self, *args, **kwargs):  # pylint: disable=arguments-differ, unused-argument
        if self.status == Webinar.UPCOMING:
            send_cancellation_emails_for_given_webinars([self])
        self.status = self.CANCELLED
        self.save()


class CancelledWebinar(Webinar):
    """
    A proxy model to represent a Cancelled Webinar
    """

    class Meta:
        proxy = True


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
