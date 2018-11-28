"""
Content Type Gating Configuration Models
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from experiments.models import ExperimentData
from student.models import CourseEnrollment
from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel
from openedx.features.course_duration_limits.config import (
    CONTENT_TYPE_GATING_FLAG,
    EXPERIMENT_ID,
    EXPERIMENT_DATA_HOLDBACK_KEY
)


@python_2_unicode_compatible
class ContentTypeGatingConfig(StackedConfigurationModel):
    """
    A ConfigurationModel used to manage configuration for Content Type Gating (Feature Based Enrollments).
    """

    STACKABLE_FIELDS = ('enabled', 'enabled_as_of', 'studio_override_enabled')

    enabled_as_of = models.DateField(
        default=None,
        null=True,
        verbose_name=_('Enabled As Of'),
        blank=True,
        help_text=_(
            'If the configuration is Enabled, then all enrollments '
            'created after this date (UTC) will be affected.'
        )
    )
    studio_override_enabled = models.NullBooleanField(
        default=None,
        verbose_name=_('Studio Override Enabled'),
        blank=True,
        help_text=_(
            'Allow Feature Based Enrollment visibility to be overriden '
            'on a per-component basis in Studio.'
        )
    )

    @classmethod
    def enabled_for_enrollment(cls, enrollment=None, user=None, course_key=None):
        """
        Return whether Content Type Gating is enabled for this enrollment.

        Content Type Gating is enabled for an enrollment if it is enabled for
        the course being enrolled in (either specifically, or via a containing context,
        such as the org, site, or globally), and if the configuration is specified to be
        ``enabled_as_of`` before the enrollment was created.

        Only one of enrollment and (user, course_key) may be specified at a time.

        Arguments:
            enrollment: The enrollment being queried.
            user: The user being queried.
            course_key: The CourseKey of the course being queried.
        """
        if CONTENT_TYPE_GATING_FLAG.is_enabled():
            return True

        if enrollment is not None and (user is not None or course_key is not None):
            raise ValueError('Specify enrollment or user/course_key, but not both')

        if enrollment is None and (user is None or course_key is None):
            raise ValueError('Both user and course_key must be specified if no enrollment is provided')

        if enrollment is None and user is None and course_key is None:
            raise ValueError('At least one of enrollment or user and course_key must be specified')

        if course_key is None:
            course_key = enrollment.course_id

        if enrollment is None:
            enrollment = CourseEnrollment.get_enrollment(user, course_key)

        # enrollment might be None if the user isn't enrolled. In that case,
        # return enablement as if the user enrolled today
        if enrollment is None:
            return cls.enabled_for_course(course_key=course_key, target_date=datetime.utcnow().date())
        else:
            # TODO: clean up as part of REV-100
            experiment_data_holdback_key = EXPERIMENT_DATA_HOLDBACK_KEY.format(user)
            is_in_holdback = False
            try:
                holdback_value = ExperimentData.objects.get(
                    user=user,
                    experiment_id=EXPERIMENT_ID,
                    key=experiment_data_holdback_key,
                ).value
                is_in_holdback = holdback_value == 'True'
            except ExperimentData.DoesNotExist:
                pass
            if is_in_holdback:
                return False
            current_config = cls.current(course_key=enrollment.course_id)
            return current_config.enabled_as_of_date(target_date=enrollment.created.date())

    @classmethod
    def enabled_for_course(cls, course_key, target_date=None):
        """
        Return whether Content Type Gating is enabled for this course as of a particular date.

        Content Type Gating is enabled for a course on a date if it is enabled either specifically,
        or via a containing context, such as the org, site, or globally, and if the configuration
        is specified to be ``enabled_as_of`` before ``target_date``.

        Only one of enrollment and (user, course_key) may be specified at a time.

        Arguments:
            course_key: The CourseKey of the course being queried.
            target_date: The date to checked enablement as of. Defaults to the current date.
        """
        if CONTENT_TYPE_GATING_FLAG.is_enabled():
            return True

        if target_date is None:
            target_date = datetime.utcnow().date()

        current_config = cls.current(course_key=course_key)
        return current_config.enabled_as_of_date(target_date=target_date)

    def clean(self):
        if self.enabled and self.enabled_as_of is None:
            raise ValidationError({'enabled_as_of': _('enabled_as_of must be set when enabled is True')})

    def enabled_as_of_date(self, target_date):
        """
        Return whether this Content Type Gating configuration context is enabled as of a date.

        Arguments:
            target_date (:class:`datetime.date`): The date that ``enabled_as_of`` must be equal to or before
        """
        if CONTENT_TYPE_GATING_FLAG.is_enabled():
            return True

        # Explicitly cast this to bool, so that when self.enabled is None the method doesn't return None
        return bool(self.enabled and self.enabled_as_of <= target_date)

    def __str__(self):
        return "ContentTypeGatingConfig(enabled={!r}, enabled_as_of={!r}, studio_override_enabled={!r})"
