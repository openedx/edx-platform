

from config_models.models import ConfigurationModel
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords


class Schedule(TimeStampedModel):
    """
    .. no_pii:
    """

    enrollment = models.OneToOneField('student.CourseEnrollment', null=False, on_delete=models.CASCADE)
    active = models.BooleanField(
        default=True,
        help_text=_('Indicates if this schedule is actively used')
    )
    start_date = models.DateTimeField(
        db_index=True,
        help_text=_('Date this schedule went into effect'),
        null=True,
        default=None
    )
    upgrade_deadline = models.DateTimeField(
        blank=True,
        db_index=True,
        null=True,
        help_text=_('Deadline by which the learner must upgrade to a verified seat')
    )
    history = HistoricalRecords()

    def get_experience_type(self):
        try:
            return self.experience.experience_type
        except ScheduleExperience.DoesNotExist:
            return ScheduleExperience.EXPERIENCES.default

    class Meta(object):
        verbose_name = _('Schedule')
        verbose_name_plural = _('Schedules')


class ScheduleConfig(ConfigurationModel):
    """
    .. no_pii:
    """
    KEY_FIELDS = ('site',)

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    create_schedules = models.BooleanField(default=False)
    enqueue_recurring_nudge = models.BooleanField(default=False)
    deliver_recurring_nudge = models.BooleanField(default=False)
    enqueue_upgrade_reminder = models.BooleanField(default=False)
    deliver_upgrade_reminder = models.BooleanField(default=False)
    enqueue_course_update = models.BooleanField(default=False)
    deliver_course_update = models.BooleanField(default=False)
    hold_back_ratio = models.FloatField(default=0)


class ScheduleExperience(models.Model):
    """
    .. no_pii:
    """
    EXPERIENCES = Choices(
        (0, 'default', u'Recurring Nudge and Upgrade Reminder'),
        (1, 'course_updates', u'Course Updates')
    )

    schedule = models.OneToOneField(Schedule, related_name='experience', on_delete=models.CASCADE)
    experience_type = models.PositiveSmallIntegerField(choices=EXPERIENCES, default=EXPERIENCES.default)
