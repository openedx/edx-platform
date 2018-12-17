"""
Content Type Gating Configuration Models
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from lms.djangoapps.courseware.masquerade import get_course_masquerade, is_masquerading_as_specific_student
from experiments.models import ExperimentData
from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel
from openedx.features.content_type_gating.helpers import has_staff_roles
from openedx.features.course_duration_limits.config import (
    CONTENT_TYPE_GATING_FLAG,
    FEATURE_BASED_ENROLLMENT_GLOBAL_KILL_FLAG,
    EXPERIMENT_ID,
    EXPERIMENT_DATA_HOLDBACK_KEY
)
from student.models import CourseEnrollment


@python_2_unicode_compatible
class ContentTypeGatingConfig(StackedConfigurationModel):
    """
    A ConfigurationModel used to manage configuration for Content Type Gating (Feature Based Enrollments).
    """

    STACKABLE_FIELDS = ('enabled', 'enabled_as_of', 'studio_override_enabled')

    enabled_as_of = models.DateTimeField(
        default=None,
        null=True,
        verbose_name=_('Enabled As Of'),
        blank=True,
        help_text=_(
            'If the configuration is Enabled, then all enrollments '
            'created after this date and time (UTC) will be affected.'
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
        if FEATURE_BASED_ENROLLMENT_GLOBAL_KILL_FLAG.is_enabled():
            return False

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

        if user is None and enrollment is not None:
            user = enrollment.user

        no_masquerade = get_course_masquerade(user, course_key) is None
        student_masquerade = is_masquerading_as_specific_student(user, course_key)
        # We can only use the user variable for the code below when the request is not in a masquerade state
        # or is masquerading as a specific user.
        # When a request is not in a masquerade state the user variable represents the correct user.
        # When a request is in a masquerade state and not masquerading as a specific user,
        # then then user variable will be the incorrect (original) user, not the masquerade user.
        # If a request is masquerading as a specific user, the user variable will represent the correct user.
        user_variable_represents_correct_user = (no_masquerade or student_masquerade)
        if user and user.id:
            # TODO: Move masquerade checks to enabled_for_enrollment from content_type_gating/partitions.py
            # TODO: Consolidate masquerade checks into shared function like has_staff_roles below
            if user_variable_represents_correct_user and has_staff_roles(user, course_key):
                return False

        # check if user is in holdback
        is_in_holdback = False
        if user and user.is_authenticated and (user_variable_represents_correct_user):
            try:
                holdback_value = ExperimentData.objects.get(
                    user=user,
                    experiment_id=EXPERIMENT_ID,
                    key=EXPERIMENT_DATA_HOLDBACK_KEY,
                ).value
                is_in_holdback = holdback_value == 'True'
            except ExperimentData.DoesNotExist:
                pass
        if is_in_holdback:
            return False

        # enrollment might be None if the user isn't enrolled. In that case,
        # return enablement as if the user enrolled today
        if enrollment is None:
            return cls.enabled_for_course(course_key=course_key, target_datetime=timezone.now())
        else:
            current_config = cls.current(course_key=enrollment.course_id)
            return current_config.enabled_as_of_datetime(target_datetime=enrollment.created)

    @classmethod
    def enabled_for_course(cls, course_key, target_datetime=None):
        """
        Return whether Content Type Gating is enabled for this course as of a particular date.

        Content Type Gating is enabled for a course on a date if it is enabled either specifically,
        or via a containing context, such as the org, site, or globally, and if the configuration
        is specified to be ``enabled_as_of`` before ``target_datetime``.

        Only one of enrollment and (user, course_key) may be specified at a time.

        Arguments:
            course_key: The CourseKey of the course being queried.
            target_datetime: The datetime to checked enablement as of. Defaults to the current date and time.
        """

        if FEATURE_BASED_ENROLLMENT_GLOBAL_KILL_FLAG.is_enabled():
            return False

        if CONTENT_TYPE_GATING_FLAG.is_enabled():
            return True

        if target_datetime is None:
            target_datetime = timezone.now()

        current_config = cls.current(course_key=course_key)
        return current_config.enabled_as_of_datetime(target_datetime=target_datetime)

    def clean(self):
        if self.enabled and self.enabled_as_of is None:
            raise ValidationError({'enabled_as_of': _('enabled_as_of must be set when enabled is True')})

    def enabled_as_of_datetime(self, target_datetime):
        """
        Return whether this Content Type Gating configuration context is enabled as of a date and time.

        Arguments:
            target_datetime (:class:`datetime.datetime`): The datetime that ``enabled_as_of`` must be equal to or before
        """

        if FEATURE_BASED_ENROLLMENT_GLOBAL_KILL_FLAG.is_enabled():
            return False

        if CONTENT_TYPE_GATING_FLAG.is_enabled():
            return True

        # Explicitly cast this to bool, so that when self.enabled is None the method doesn't return None
        return bool(self.enabled and self.enabled_as_of <= target_datetime)

    def __str__(self):
        return "ContentTypeGatingConfig(enabled={!r}, enabled_as_of={!r}, studio_override_enabled={!r})".format(
            self.enabled,
            self.enabled_as_of,
            self.studio_override_enabled,
        )
