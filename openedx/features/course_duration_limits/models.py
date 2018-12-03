"""
Course Duration Limit Configuration Models
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from xmodule.partitions.partitions import ENROLLMENT_TRACK_PARTITION_ID

from course_modes.models import CourseMode
from lms.djangoapps.courseware.masquerade import get_masquerade_role, get_course_masquerade, \
    is_masquerading_as_specific_student

from experiments.models import ExperimentData
from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel
from openedx.features.content_type_gating.partitions import CONTENT_GATING_PARTITION_ID, CONTENT_TYPE_GATE_GROUP_IDS
from openedx.features.course_duration_limits.config import (
    CONTENT_TYPE_GATING_FLAG,
    EXPERIMENT_ID,
    EXPERIMENT_DATA_HOLDBACK_KEY
)
from student.models import CourseEnrollment
from student.roles import CourseBetaTesterRole, CourseInstructorRole, CourseStaffRole


@python_2_unicode_compatible
class CourseDurationLimitConfig(StackedConfigurationModel):
    """
    Configuration to manage the Course Duration Limit facility.
    """

    STACKABLE_FIELDS = ('enabled', 'enabled_as_of')

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

    @classmethod
    def enabled_for_enrollment(cls, enrollment=None, user=None, course_key=None):
        """
        Return whether Course Duration Limits are enabled for this enrollment.

        Course Duration Limits are enabled for an enrollment if they are enabled for
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

        # if the user is has a role of staff, instructor or beta tester their access should not expire
        if user is None and enrollment is not None:
            user = enrollment.user

        if user:
            course_masquerade = get_course_masquerade(user, course_key)
            if course_masquerade:
                verified_mode_id = settings.COURSE_ENROLLMENT_MODES.get(CourseMode.VERIFIED, {}).get('id')
                is_verified = (course_masquerade.user_partition_id == ENROLLMENT_TRACK_PARTITION_ID
                               and course_masquerade.group_id == verified_mode_id)
                is_full_access = (course_masquerade.user_partition_id == CONTENT_GATING_PARTITION_ID
                                  and course_masquerade.group_id == CONTENT_TYPE_GATE_GROUP_IDS['full_access'])
                is_staff = get_masquerade_role(user, course_key) == 'staff'
                if is_verified or is_full_access or is_staff:
                    return False
            else:
                staff_role = CourseStaffRole(course_key).has_user(user)
                instructor_role = CourseInstructorRole(course_key).has_user(user)
                beta_tester_role = CourseBetaTesterRole(course_key).has_user(user)

                if staff_role or instructor_role or beta_tester_role:
                    return False

        # enrollment might be None if the user isn't enrolled. In that case,
        # return enablement as if the user enrolled today
        if enrollment is None:
            return cls.enabled_for_course(course_key=course_key, target_datetime=timezone.now())
        else:
            # TODO: clean up as part of REV-100
            experiment_data_holdback_key = EXPERIMENT_DATA_HOLDBACK_KEY.format(user)
            is_in_holdback = False
            no_masquerade = get_course_masquerade(user, course_key) is None
            student_masquerade = is_masquerading_as_specific_student(user, course_key)
            if user and (no_masquerade or student_masquerade):
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
            return current_config.enabled_as_of_datetime(target_datetime=enrollment.created)

    @classmethod
    def enabled_for_course(cls, course_key, target_datetime=None):
        """
        Return whether Course Duration Limits are enabled for this course as of a particular date.

        Course Duration Limits are enabled for a course on a date if they are enabled either specifically,
        or via a containing context, such as the org, site, or globally, and if the configuration
        is specified to be ``enabled_as_of`` before ``target_datetime``.

        Only one of enrollment and (user, course_key) may be specified at a time.

        Arguments:
            course_key: The CourseKey of the course being queried.
            target_datetime: The datetime to checked enablement as of. Defaults to the current date and time.
        """
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
        Return whether this Course Duration Limit configuration context is enabled as of a date and time.

        Arguments:
            target_datetime (:class:`datetime.datetime`): The datetime that ``enabled_as_of`` must be equal to or before
        """
        if CONTENT_TYPE_GATING_FLAG.is_enabled():
            return True

        # Explicitly cast this to bool, so that when self.enabled is None the method doesn't return None
        return bool(self.enabled and self.enabled_as_of <= target_datetime)

    def __str__(self):
        return "CourseDurationLimits(enabled={!r}, enabled_as_of={!r})".format(
            self.enabled,
            self.enabled_as_of,
        )
