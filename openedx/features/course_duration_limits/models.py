"""
Course Duration Limit Configuration Models
"""

# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.courseware.masquerade import (
    get_course_masquerade,
    get_masquerade_role,
    is_masquerading_as_specific_student
)
from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel
from openedx.core.djangoapps.config_model_utils.utils import is_in_holdback
from openedx.features.content_type_gating.helpers import (
    CONTENT_GATING_PARTITION_ID,
    CONTENT_TYPE_GATE_GROUP_IDS,
    correct_modes_for_fbe
)
from student.models import CourseEnrollment
from student.role_helpers import has_staff_roles
from xmodule.partitions.partitions import ENROLLMENT_TRACK_PARTITION_ID


@python_2_unicode_compatible
class CourseDurationLimitConfig(StackedConfigurationModel):
    """
    Configuration to manage the Course Duration Limit facility.

    .. no_pii:
    """

    STACKABLE_FIELDS = ('enabled', 'enabled_as_of')

    enabled_as_of = models.DateTimeField(
        default=None,
        null=True,
        verbose_name=_('Enabled As Of'),
        blank=True,
        help_text=_(
            'If the configuration is Enabled, then all enrollments '
            'created after this date and time (user local time) will be affected.'
        )
    )

    @classmethod
    def has_full_access_role_in_masquerade(cls, user, course_key, course_masquerade):
        """
        When masquerading, the course duration limits will never trigger the course to expire, redirecting the user.
        The roles of the masquerade user are still used to determine whether the course duration limit banner displays.
        Another banner also displays if the course is expired for the masquerade user.
        Both banners will appear if the masquerade user does not have any of the following roles:
        Staff, Instructor, Beta Tester, Forum Community TA, Forum Group Moderator, Forum Moderator, Forum Administrator
        """
        masquerade_role = get_masquerade_role(user, course_key)
        verified_mode_id = settings.COURSE_ENROLLMENT_MODES.get(CourseMode.VERIFIED, {}).get('id')
        # Masquerading users can select the the role of a verified users without selecting a specific user
        is_verified = (course_masquerade.user_partition_id == ENROLLMENT_TRACK_PARTITION_ID
                       and course_masquerade.group_id == verified_mode_id)
        # Masquerading users can select the role of staff without selecting a specific user
        is_staff = masquerade_role == 'staff'
        # Masquerading users can select other full access roles for which content type gating is disabled
        is_full_access = (course_masquerade.user_partition_id == CONTENT_GATING_PARTITION_ID
                          and course_masquerade.group_id == CONTENT_TYPE_GATE_GROUP_IDS['full_access'])
        # When masquerading as a specific user, we can check that user's staff roles as we would with a normal user
        is_staff_role = False
        if course_masquerade.user_name:
            is_staff_role = has_staff_roles(user, course_key)

        if is_verified or is_full_access or is_staff or is_staff_role:
            return True
        return False

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

        if user and user.id:
            course_masquerade = get_course_masquerade(user, course_key)
            if course_masquerade:
                if cls.has_full_access_role_in_masquerade(user, course_key, course_masquerade):
                    return False
            elif has_staff_roles(user, course_key):
                return False

        is_masquerading = get_course_masquerade(user, course_key)
        no_masquerade = is_masquerading is None
        student_masquerade = is_masquerading_as_specific_student(user, course_key)

        # check if user is in holdback
        if (no_masquerade or student_masquerade) and is_in_holdback(user):
            return False

        not_student_masquerade = is_masquerading and not student_masquerade

        # enrollment might be None if the user isn't enrolled. In that case,
        # return enablement as if the user enrolled today
        # When masquerading as a user group rather than a specific learner,
        # course duration limits will be on if they are on for the course.
        # When masquerading as a specific learner, course duration limits
        # will be on if they are currently on for the learner.
        if enrollment is None or not_student_masquerade:
            # we bypass enabled_for_course here and use enabled_as_of_datetime directly
            # because the correct_modes_for_fbe for FBE check contained in enabled_for_course
            # is redundant with checks done upstream of this code
            target_datetime = timezone.now()
        else:
            target_datetime = enrollment.created
        current_config = cls.current(course_key=course_key)
        return current_config.enabled_as_of_datetime(target_datetime=target_datetime)

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
        if not correct_modes_for_fbe(course_key):
            return False

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

        # Explicitly cast this to bool, so that when self.enabled is None the method doesn't return None
        return bool(self.enabled and self.enabled_as_of <= target_datetime)

    def __str__(self):
        return "CourseDurationLimits(enabled={!r}, enabled_as_of={!r})".format(
            self.enabled,
            self.enabled_as_of,
        )
