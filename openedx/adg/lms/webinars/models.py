"""
All models for webinars app
"""
from itertools import chain

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from openedx.adg.lms.applications.helpers import validate_file_size
from openedx.core.djangoapps.theming.helpers import get_current_request

from .constants import ALLOWED_BANNER_EXTENSIONS, BANNER_MAX_SIZE, WEBINARS_TIME_FORMAT
from .helpers import cancel_reminders_for_given_webinars, send_cancellation_emails_for_given_webinars
from .managers import WebinarRegistrationManager


class WebinarQuerySet(models.QuerySet):
    """
    Custom QuerySet that does not allow Webinars to be deleted from the database, instead marks the status of the
    deleted Webinars as `Cancelled`
    """

    def delete(self):
        cancelled_upcoming_webinars = self.filter(
            status=Webinar.UPCOMING).select_related('presenter').prefetch_related('co_hosts', 'panelists')
        send_cancellation_emails_for_given_webinars(cancelled_upcoming_webinars)
        cancel_reminders_for_given_webinars(cancelled_upcoming_webinars)
        self.update(status=Webinar.CANCELLED)


class Webinar(TimeStampedModel):
    """
    Model to create a webinar
    """

    start_time = models.DateTimeField(verbose_name=_('Start Time'), )
    end_time = models.DateTimeField(verbose_name=_('End Time'), )

    title = models.CharField(verbose_name=_('Title'), max_length=100, )
    description = models.TextField(verbose_name=_('Description'), )
    presenter = models.ForeignKey(
        User, verbose_name=_('Presenter'), on_delete=models.CASCADE, related_name='webinar_presenter',
    )
    meeting_link = models.URLField(verbose_name=_('Meeting Link'), )
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

    def to_dict(self):
        return {
            'webinar_id': self.id,
            'webinar_title': self.title,
            'webinar_description': self.description,
            'webinar_start_time': self.start_time.strftime(WEBINARS_TIME_FORMAT),
            'webinar_meeting_link': self.meeting_link,
        }

    def clean(self):
        """
        Adding custom validation on start & end time and banner size
        """
        super().clean()

        errors = {}
        if self.start_time and self.start_time < now():
            errors['start_time'] = _('Start date/time should be in future')

        if self.end_time and self.end_time < now():
            errors['end_time'] = _('End date/time should be in future')

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            errors['end_time'] = _('End date/time must be greater than start date/time')

        if self.banner:
            error_message = validate_file_size(self.banner, BANNER_MAX_SIZE)
            if error_message:
                errors['banner'] = error_message

        if errors:
            raise ValidationError(errors)

    def delete(self, *args, **kwargs):  # pylint: disable=arguments-differ, unused-argument
        if self.status == Webinar.UPCOMING:
            send_cancellation_emails_for_given_webinars([self])
            cancel_reminders_for_given_webinars([self])
        self.status = self.CANCELLED
        self.save()

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._loaded_values = dict(zip(field_names, values))  # pylint: disable=protected-access

        return instance

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Extension of save for webinar to set the created_by and modified_by fields and reschedule reminders.
        """
        from openedx.adg.lms.webinars.tasks import task_reschedule_webinar_reminders

        request = get_current_request()
        if request:
            if hasattr(self, 'created_by'):
                self.modified_by = request.user
            else:
                self.created_by = request.user

        super(Webinar, self).save(
            force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields
        )

        old_values = getattr(self, '_loaded_values', {})
        if old_values and old_values.get('start_time') != self.start_time:
            task_reschedule_webinar_reminders.delay(self.to_dict())

    def webinar_team(self):
        return set(chain(self.co_hosts.all(), self.panelists.all(), {self.presenter}))


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

    is_registered = models.BooleanField(default=False, verbose_name=_('Registered'),)
    is_team_member_registration = models.BooleanField(
        default=False, verbose_name=_('Is Presenter, Co-Host, or Panelist'),
    )

    starting_soon_mandrill_reminder_id = models.CharField(
        default='', max_length=255, verbose_name=_('Scheduled Starting Soon Reminder Id On Mandrill'),
    )
    week_before_mandrill_reminder_id = models.CharField(
        default='', max_length=255, verbose_name=_('Scheduled Week Before Reminder Id On Mandrill'),
    )

    objects = WebinarRegistrationManager()

    class Meta:
        app_label = 'webinars'
        unique_together = ('webinar', 'user')

    def __str__(self):
        return f'User {self.user}, Webinar {self.webinar}'

    @classmethod
    def create_team_registrations(cls, team_members, webinar, **kwargs):
        """
        Create or update webinar team registrations.

        Args:
            team_members (list): List of users for which team registrations will be added.
            webinar (Webinar): Webinar for which registrations will be added.
            is_webinar_team (bool): Are registrations for webinar team members.
            **kwargs (dict): Dictionary of values to be set for the registrations.

        Returns:
            None
        """
        for member in team_members:
            WebinarRegistration.objects.update_or_create(
                webinar=webinar, user=member, defaults={
                    'is_team_member_registration': True,
                    **kwargs
                }
            )

    @classmethod
    def remove_team_registrations(cls, team_members, webinar):
        """
        Marks `is_team_member_registration=False` for the given members.

        Args:
            team_members (list): List of team members for which `is_team_member_registration` will be marked as False.
            webinar (Webinar): Webinar for which registrations will be updated.

        Returns:
            None
        """
        cls.objects.filter(
            webinar=webinar, user__in=team_members
        ).update(
            is_team_member_registration=False
        )
