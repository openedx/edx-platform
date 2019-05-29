"""
Content Type Gating Configuration Models
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
    get_masquerading_user_group,
    is_masquerading_as_specific_student
)
from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel
from openedx.core.djangoapps.config_model_utils.utils import is_in_holdback
from openedx.features.content_type_gating.helpers import FULL_ACCESS, LIMITED_ACCESS, correct_modes_for_fbe
from student.models import CourseEnrollment
from student.role_helpers import has_staff_roles
from xmodule.partitions.partitions import ENROLLMENT_TRACK_PARTITION_ID


@python_2_unicode_compatible
class ContentTypeGatingConfig(StackedConfigurationModel):
    """
    A ConfigurationModel used to manage configuration for Content Type Gating (Feature Based Enrollments).

    .. no_pii:
    """

    STACKABLE_FIELDS = ('enabled', 'enabled_as_of', 'studio_override_enabled')

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
    def has_full_access_role_in_masquerade(cls, user, course_key, course_masquerade, student_masquerade,
                                           user_partition):
        """
        The roles of the masquerade user are used to determine whether the content gate displays.
        The gate will not appear if the masquerade user has any of the following roles:
        Staff, Instructor, Beta Tester, Forum Community TA, Forum Group Moderator, Forum Moderator, Forum Administrator
        """
        if student_masquerade:
            # If a request is masquerading as a specific user, the user variable will represent the correct user.
            if user and user.id and has_staff_roles(user, course_key):
                return True
        elif user_partition:
            # If the current user is masquerading as a generic student in a specific group,
            # then return the value based on that group.
            masquerade_group = get_masquerading_user_group(course_key, user, user_partition)
            if masquerade_group is None:
                audit_mode_id = settings.COURSE_ENROLLMENT_MODES.get(CourseMode.AUDIT, {}).get('id')
                # We are checking the user partition id here because currently content
                # cannot have both the enrollment track partition and content gating partition
                # configured simultaneously. We may change this in the future and allow
                # configuring both partitions on content and selecting both partitions in masquerade.
                if course_masquerade.user_partition_id == ENROLLMENT_TRACK_PARTITION_ID:
                    return course_masquerade.group_id != audit_mode_id
            elif masquerade_group is FULL_ACCESS:
                return True
            elif masquerade_group is LIMITED_ACCESS:
                return False

    @classmethod
    def enabled_for_enrollment(cls, enrollment=None, user=None, course_key=None, user_partition=None):
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

        course_masquerade = get_course_masquerade(user, course_key)
        no_masquerade = course_masquerade is None
        student_masquerade = is_masquerading_as_specific_student(user, course_key)
        user_variable_represents_correct_user = (no_masquerade or student_masquerade)

        if course_masquerade:
            if cls.has_full_access_role_in_masquerade(user, course_key, course_masquerade, student_masquerade,
                                                      user_partition):
                return False
        # When a request is not in a masquerade state the user variable represents the correct user.
        elif user and user.id and has_staff_roles(user, course_key):
            return False

        # check if user is in holdback
        if user_variable_represents_correct_user and is_in_holdback(user):
            return False

        if not correct_modes_for_fbe(course_key, enrollment, user):
            return False

        # enrollment might be None if the user isn't enrolled. In that case,
        # return enablement as if the user enrolled today
        # Also, ignore enrollment creation date if the user is masquerading.
        if enrollment is None or course_masquerade:
            target_datetime = timezone.now()
        else:
            target_datetime = enrollment.created
        current_config = cls.current(course_key=course_key)
        return current_config.enabled_as_of_datetime(target_datetime=target_datetime)

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
        Return whether this Content Type Gating configuration context is enabled as of a date and time.

        Arguments:
            target_datetime (:class:`datetime.datetime`): The datetime that ``enabled_as_of`` must be equal to or before
        """

        # Explicitly cast this to bool, so that when self.enabled is None the method doesn't return None
        return bool(self.enabled and self.enabled_as_of <= target_datetime)

    def __str__(self):
        return "ContentTypeGatingConfig(enabled={!r}, enabled_as_of={!r}, studio_override_enabled={!r})".format(
            self.enabled,
            self.enabled_as_of,
            self.studio_override_enabled,
        )
