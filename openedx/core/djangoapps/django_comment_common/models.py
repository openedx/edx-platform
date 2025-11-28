# pylint: disable=missing-docstring,unused-argument


import json
import logging

from config_models.models import ConfigurationModel
from django.conf import settings
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.utils.translation import gettext_noop
from jsonfield.fields import JSONField
from opaque_keys.edx.django.models import CourseKeyField
from model_utils.models import TimeStampedModel

from openedx.core.djangoapps.xmodule_django.models import NoneToEmptyManager
from openedx.core.lib.cache_utils import request_cached
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import GlobalStaff
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.exceptions import ItemNotFoundError  # lint-amnesty, pylint: disable=wrong-import-order

FORUM_ROLE_ADMINISTRATOR = gettext_noop('Administrator')
FORUM_ROLE_MODERATOR = gettext_noop('Moderator')
FORUM_ROLE_GROUP_MODERATOR = gettext_noop('Group Moderator')
FORUM_ROLE_COMMUNITY_TA = gettext_noop('Community TA')
FORUM_ROLE_STUDENT = gettext_noop('Student')


@receiver(post_save, sender=CourseEnrollment)
def assign_default_role_on_enrollment(sender, instance, **kwargs):
    """
    Assign forum default role 'Student'
    """
    # The code below would remove all forum Roles from a user when they unenroll
    # from a course. Concerns were raised that it should apply only to students,
    # or that even the history of student roles is important for research
    # purposes. Since this was new functionality being added in this release,
    # I'm just going to comment it out for now and let the forums team deal with
    # implementing the right behavior.
    #
    # # We've unenrolled the student, so remove all roles for this course
    # if not instance.is_active:
    #     course_roles = list(Role.objects.filter(course_id=instance.course_id))
    #     instance.user.roles.remove(*course_roles)
    #     return

    # We've enrolled the student, so make sure they have the Student role
    assign_default_role(instance.course_id, instance.user)


def assign_default_role(course_id, user):
    """
    Assign forum default role 'Student' to user
    """
    assign_role(course_id, user, FORUM_ROLE_STUDENT)


def assign_role(course_id, user, rolename):
    """
    Assign forum role `rolename` to user
    """
    role, created = Role.objects.get_or_create(course_id=course_id, name=rolename)
    if created:
        logging.info(f"EDUCATOR-1635: Created role {role} for course {course_id}")
    user.roles.add(role)


class Role(models.Model):
    """
    Maps users to django_comment_client roles for a given course

    .. no_pii:
    """

    objects = NoneToEmptyManager()

    name = models.CharField(max_length=30, null=False, blank=False)
    users = models.ManyToManyField(User, related_name="roles")
    course_id = CourseKeyField(max_length=255, blank=True, db_index=True)

    class Meta:
        # use existing table that was originally created from lms.djangoapps.discussion.django_comment_client app
        db_table = 'django_comment_client_role'

    def __str__(self):
        return self.name + " for " + (str(self.course_id) if self.course_id else "all courses")

    # TODO the name of this method is a little bit confusing,
    # since it's one-off and doesn't handle inheritance later
    def inherit_permissions(self, role):
        """
        Make this role inherit permissions from the given role.
        Permissions are only added, not removed. Does not handle inheritance.
        """
        if role.course_id and role.course_id != self.course_id:
            logging.warning(
                "%s cannot inherit permissions from %s due to course_id inconsistency",
                self,
                role,
            )
        for per in role.permissions.all():
            self.add_permission(per)

    def add_permission(self, permission):
        self.permissions.add(Permission.objects.get_or_create(name=permission)[0])  # lint-amnesty, pylint: disable=no-member

    def has_permission(self, permission):
        """
        Returns True if this role has the given permission, False otherwise.
        """
        course = modulestore().get_course(self.course_id)
        if course is None:
            raise ItemNotFoundError(self.course_id)
        if permission_blacked_out(course, {self.name}, permission):
            return False

        return self.permissions.filter(name=permission).exists()

    @staticmethod
    def user_has_role_for_course(user, course_id, role_names):
        """
        Returns True if the user has one of the given roles for the given course
        """
        return Role.objects.filter(course_id=course_id, name__in=role_names, users=user).exists()


class Permission(models.Model):
    """
    Permissions for django_comment_client

    .. no_pii:
    """
    name = models.CharField(max_length=30, null=False, blank=False, primary_key=True)
    roles = models.ManyToManyField(Role, related_name="permissions")

    class Meta:
        # use existing table that was originally created from lms.djangoapps.discussion.django_comment_client app
        db_table = 'django_comment_client_permission'

    def __str__(self):
        return self.name


def permission_blacked_out(course, role_names, permission_name):
    """
    Returns true if a user in course with the given roles would have permission_name blacked out.

    This will return true if it is a permission that the user might have normally had for the course, but does not have
    right this moment because we are in a discussion blackout period (as defined by the settings on the course block).
    Namely, they can still view, but they can't edit, update, or create anything. This only applies to students, as
    moderators of any kind still have posting privileges during discussion blackouts.
    """
    return (
        not course.forum_posts_allowed and
        role_names == {FORUM_ROLE_STUDENT} and
        any(permission_name.startswith(prefix) for prefix in ['edit', 'update', 'create'])
    )


def all_permissions_for_user_in_course(user, course_id):
    """
    Returns all the permissions the user has in the given course.
    """
    if not user.is_authenticated:
        return {}

    course = modulestore().get_course(course_id)
    if course is None:
        raise ItemNotFoundError(course_id)

    roles = Role.objects.filter(users=user, course_id=course_id)
    role_names = {role.name for role in roles}

    permission_names = set()
    for role in roles:
        # Intentional n+1 query pattern to get permissions for each role because
        # Aurora's query optimizer can't handle the join proplerly on 30M+ row
        # tables (EDUCATOR-3374). Fortunately, there are very few forum roles.
        for permission in role.permissions.all():
            if not permission_blacked_out(course, role_names, permission.name):
                permission_names.add(permission.name)

    # Prevent a circular import
    from openedx.core.djangoapps.django_comment_common.utils import GLOBAL_STAFF_ROLE_PERMISSIONS

    if GlobalStaff().has_user(user):
        for permission in GLOBAL_STAFF_ROLE_PERMISSIONS:
            permission_names.add(permission)

    return permission_names


class ForumsConfig(ConfigurationModel):
    """
    Config for the connection to the cs_comments_service forums backend.

    .. no_pii:
    """

    connection_timeout = models.FloatField(
        default=5.0,
        help_text="Seconds to wait when trying to connect to the comment service.",
    )

    class Meta(ConfigurationModel.Meta):
        # use existing table that was originally created from django_comment_common app
        db_table = 'django_comment_common_forumsconfig'

    @property
    def api_key(self):
        """The API key used to authenticate to the comments service."""
        return getattr(settings, "COMMENTS_SERVICE_KEY", None)

    def __str__(self):
        """
        Simple representation so the admin screen looks less ugly.
        """
        return f"ForumsConfig: timeout={self.connection_timeout}"


class CourseDiscussionSettings(models.Model):
    """
    Settings for course discussions

    .. no_pii:
    """
    course_id = CourseKeyField(
        unique=True,
        max_length=255,
        db_index=True,
        help_text="Which course are these settings associated with?",
    )
    discussions_id_map = JSONField(
        null=True,
        blank=True,
        help_text="Key/value store mapping discussion IDs to discussion XBlock usage keys.",
    )
    always_divide_inline_discussions = models.BooleanField(default=False)
    reported_content_email_notifications = models.BooleanField(default=False)
    _divided_discussions = models.TextField(db_column='divided_discussions', null=True, blank=True)  # JSON list

    COHORT = 'cohort'
    ENROLLMENT_TRACK = 'enrollment_track'
    NONE = 'none'
    ASSIGNMENT_TYPE_CHOICES = ((NONE, 'None'), (COHORT, 'Cohort'), (ENROLLMENT_TRACK, 'Enrollment Track'))
    division_scheme = models.CharField(max_length=20, choices=ASSIGNMENT_TYPE_CHOICES, default=NONE)

    class Meta:
        # use existing table that was originally created from django_comment_common app
        db_table = 'django_comment_common_coursediscussionsettings'

    @property
    def divided_discussions(self):
        """
        Jsonify the divided_discussions
        """
        return json.loads(self._divided_discussions)

    @divided_discussions.setter
    def divided_discussions(self, value):
        """
        Un-Jsonify the divided_discussions
        """
        self._divided_discussions = json.dumps(value)

    @request_cached()
    @classmethod
    def get(cls, course_key):
        """
        Get and/or create settings
        """
        try:
            course_discussion_settings = cls.objects.get(course_id=course_key)
        except cls.DoesNotExist:
            from openedx.core.djangoapps.course_groups.cohorts import get_legacy_discussion_settings
            legacy_discussion_settings = get_legacy_discussion_settings(course_key)
            course_discussion_settings, _ = cls.objects.get_or_create(
                course_id=course_key,
                defaults={
                    'always_divide_inline_discussions': legacy_discussion_settings['always_cohort_inline_discussions'],
                    'divided_discussions': legacy_discussion_settings['cohorted_discussions'],
                    'division_scheme': cls.COHORT if legacy_discussion_settings['is_cohorted'] else cls.NONE
                },
            )
        return course_discussion_settings

    def update(self, validated_data: dict):
        """
        Set discussion settings for a course

        Returns:
            A CourseDiscussionSettings object
        """
        fields = {
            'division_scheme': (str,)[0],
            'always_divide_inline_discussions': bool,
            'divided_discussions': list,
            'reported_content_email_notifications': bool,
        }
        for field, field_type in fields.items():
            if field in validated_data:
                if not isinstance(validated_data[field], field_type):
                    raise ValueError(f"Incorrect field type for `{field}`. Type must be `{field_type.__name__}`")
                setattr(self, field, validated_data[field])
        self.save()
        return self


class DiscussionsIdMapping(models.Model):
    """
    This model is a performance optimization, updated on course publish.

    .. no_pii:
    """
    course_id = CourseKeyField(db_index=True, primary_key=True, max_length=255)
    mapping = JSONField(
        help_text="Key/value store mapping discussion IDs to discussion XBlock usage keys.",
    )

    class Meta:
        # use existing table that was originally created from django_comment_common app
        db_table = 'django_comment_common_discussionsidmapping'

    @classmethod
    def update_mapping(cls, course_key, discussions_id_map):
        """Update the mapping of discussions IDs to XBlock usage key strings."""
        mapping_entry, created = cls.objects.get_or_create(
            course_id=course_key,
            defaults={
                'mapping': discussions_id_map,
            },
        )
        if not created:
            mapping_entry.mapping = discussions_id_map
            mapping_entry.save()


class DiscussionMute(TimeStampedModel):
    """
    Tracks muted users in discussions.
    A mute can be personal or course-wide.
    """

    class Scope(models.TextChoices):
        PERSONAL = "personal", "Personal"
        COURSE = "course", "Course-wide"

    muted_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='muted_by_users',
        help_text='User being muted',
        db_index=True,
    )
    muted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='muted_users',
        help_text='User performing the mute',
        db_index=True,
    )
    unmuted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mute_unactions",
        help_text="User who performed the unmute action"
    )
    course_id = CourseKeyField(
        max_length=255,
        db_index=True,
        help_text='Course in which mute applies'
    )
    scope = models.CharField(
        max_length=10,
        choices=Scope.choices,
        default=Scope.PERSONAL,
        help_text='Scope of the mute (personal or course-wide)',
        db_index=True,
    )
    reason = models.TextField(
        blank=True,
        help_text='Optional reason for muting'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the mute is currently active'
    )

    muted_at = models.DateTimeField(auto_now_add=True)
    unmuted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'discussion_user_mute'
        constraints = [
            # Only one active personal mute per (muted_by → muted_user) in a course
            models.UniqueConstraint(
                fields=['muted_user', 'muted_by', 'course_id', 'scope'],
                condition=Q(is_active=True, scope='personal'),
                name='unique_active_personal_mute'
            ),
            # Only one active course-wide mute per user per course
            models.UniqueConstraint(
                fields=['muted_user', 'course_id'],
                condition=Q(is_active=True, scope='course'),
                name='unique_active_course_mute'
            ),
        ]

        indexes = [
            models.Index(fields=['muted_user', 'course_id', 'is_active']),
            models.Index(fields=['muted_by', 'course_id', 'scope']),
            models.Index(fields=['scope', 'course_id', 'is_active']),
        ]

    def clean(self):
        """Additional validation depending on mute scope."""
        super().clean()

        # Personal mute must have a muted_by different from muted_user
        if self.scope == self.Scope.PERSONAL:
            if self.muted_by == self.muted_user:
                raise ValidationError("Personal mute cannot be self-applied.")

        # Course-wide mute must not be self-applied
        if self.scope == self.Scope.COURSE:
            if self.muted_by == self.muted_user:
                raise ValidationError("Course-wide mute cannot be self-applied.")

    def __str__(self):
        return f"{self.muted_by} muted {self.muted_user} in {self.course_id} ({self.scope})"


class DiscussionMuteException(TimeStampedModel):
    """
    Per-user exception for course-wide mutes.
    Allows a specific user to unmute someone while the rest of the course remains muted.
    """

    muted_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mute_exceptions_for',
        help_text='User who is globally muted in this course',
        db_index=True,
    )
    exception_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mute_exceptions',
        help_text='User who unmuted the muted_user for themselves',
        db_index=True,
    )
    course_id = CourseKeyField(
        max_length=255,
        help_text='Course where the exception applies',
        db_index=True,
    )

    class Meta:
        db_table = 'discussion_mute_exception'
        unique_together = [
            ['muted_user', 'exception_user', 'course_id']
        ]
        indexes = [
            models.Index(fields=['muted_user', 'course_id']),
            models.Index(fields=['exception_user', 'course_id']),
        ]

    def clean(self):
        """Ensure exception is only created if a course-wide mute is active."""
        super().clean()

        has_coursewide_mute = DiscussionMute.objects.filter(
            muted_user=self.muted_user,
            course_id=self.course_id,
            scope=DiscussionMute.Scope.COURSE,
            is_active=True
        ).exists()

        if not has_coursewide_mute:
            raise ValidationError(
                "Exception can only be created for an active course-wide mute."
            )

    def __str__(self):
        return f"{self.exception_user} unmuted {self.muted_user} in {self.course_id}"

class DiscussionModerationLog(TimeStampedModel):
    """
    Logs moderation actions such as mute, unmute, and mute_and_report.
    """

    class ActionType(models.TextChoices):
        MUTE = "mute", "Mute"
        UNMUTE = "unmute", "Unmute"
        MUTE_AND_REPORT = "mute_and_report", "Mute and Report"

    class Scope(models.TextChoices):
        PERSONAL = "personal", "Personal"
        COURSE = "course", "Course-wide"

    # Convenience constants for backward compatibility
    ACTION_MUTE = ActionType.MUTE
    ACTION_UNMUTE = ActionType.UNMUTE
    ACTION_MUTE_AND_REPORT = ActionType.MUTE_AND_REPORT

    action_type = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        help_text='Type of moderation action performed',
        db_index=True,
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='discussion_moderation_targets',
        help_text='User on whom the action was performed',
        db_index=True,
    )
    moderator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='discussion_moderation_logs',
        help_text='User performing the moderation action',
        db_index=True,
    )
    course_id = CourseKeyField(
        max_length=255,
        help_text='Course where the action was performed',
        db_index=True,
    )
    scope = models.CharField(
        max_length=10,
        choices=Scope.choices,
        default=Scope.PERSONAL,
        help_text='Scope of the moderation action'
    )
    reason = models.TextField(
        blank=True,
        help_text='Optional reason for moderation'
    )
    metadata = JSONField(
        default=dict,
        blank=True,
        help_text='Additional metadata for the action'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When this action was performed'
    )

    class Meta:
        db_table = 'discussion_moderation_log'
        indexes = [
            models.Index(fields=['target_user', 'course_id', 'timestamp']),
            models.Index(fields=['moderator', 'course_id', 'action_type']),
            models.Index(fields=['course_id', 'action_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.moderator} performed {self.action_type} on {self.target_user} in {self.course_id}"
