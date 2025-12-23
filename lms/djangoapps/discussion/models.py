"""
Django models for discussion moderation features.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField

User = get_user_model()


class DiscussionBan(TimeStampedModel):
    """
    Tracks users banned from course or organization discussions.

    Uses edX standard patterns:
    - TimeStampedModel for created/modified timestamps
    - CourseKeyField for course_id
    - Soft delete pattern with is_active flag
    """

    SCOPE_COURSE = 'course'
    SCOPE_ORGANIZATION = 'organization'
    SCOPE_CHOICES = [
        (SCOPE_COURSE, _('Course')),
        (SCOPE_ORGANIZATION, _('Organization')),
    ]

    # Core Fields
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='discussion_bans',
        db_index=True,
    )
    course_id = CourseKeyField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        help_text="Specific course for course-level bans, NULL for org-level bans"
    )
    org_key = models.CharField(
        max_length=255,
        db_index=True,
        null=True,
        blank=True,
        help_text="Organization name for org-level bans (e.g., 'HarvardX'), NULL for course-level"
    )
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default=SCOPE_COURSE,
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)

    # Metadata
    banned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bans_issued',
    )
    reason = models.TextField()
    banned_at = models.DateTimeField(auto_now_add=True)
    unbanned_at = models.DateTimeField(null=True, blank=True)
    unbanned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bans_reversed',
    )

    class Meta:
        db_table = 'discussion_user_ban'
        indexes = [
            models.Index(fields=['user', 'is_active'], name='idx_user_active'),
            models.Index(fields=['course_id', 'is_active'], name='idx_course_active'),
            models.Index(fields=['org_key', 'is_active'], name='idx_org_active'),
            models.Index(fields=['scope', 'is_active'], name='idx_scope_active'),
        ]
        constraints = [
            # Prevent duplicate course-level bans
            models.UniqueConstraint(
                fields=['user', 'course_id'],
                condition=models.Q(is_active=True, scope='course'),
                name='unique_active_course_ban'
            ),
            # Prevent duplicate org-level bans
            models.UniqueConstraint(
                fields=['user', 'org_key'],
                condition=models.Q(is_active=True, scope='organization'),
                name='unique_active_org_ban'
            ),
            # Note: Scope-based field validation is done in clean() method
            # CheckConstraints don't work well with CourseKeyField due to opaque_keys limitations
        ]
        verbose_name = _('Discussion Ban')
        verbose_name_plural = _('Discussion Bans')

    def __str__(self):
        if self.scope == self.SCOPE_COURSE:
            return f"Ban: {self.user.username} in {self.course_id} (course-level)"
        else:
            return f"Ban: {self.user.username} in {self.org_key} (org-level)"

    def clean(self):
        """Validate scope-based field requirements."""
        super().clean()
        if self.scope == self.SCOPE_COURSE:
            if not self.course_id:
                raise ValidationError(_("Course-level bans require course_id"))
        elif self.scope == self.SCOPE_ORGANIZATION:
            if not self.org_key:
                raise ValidationError(_("Organization-level bans require organization"))
            if self.course_id:
                raise ValidationError(_("Organization-level bans should not have course_id set"))

    @classmethod
    def is_user_banned(cls, user, course_id, check_org=True):
        """
        Check if user is banned from discussions.

        Priority:
        1. Check for course-level exception to org ban (allows user)
        2. Organization-level ban (applies to all courses in org)
        3. Course-level ban (applies to specific course)

        Args:
            user: User object
            course_id: CourseKey or string
            check_org: If True, also check organization-level bans

        Returns:
            bool: True if user has active ban
        """
        from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
        from opaque_keys.edx.keys import CourseKey

        # Normalize course_id to CourseKey
        if isinstance(course_id, str):
            course_id = CourseKey.from_string(course_id)

        # Check organization-level ban first (higher priority)
        if check_org:
            # Try to get organization from CourseOverview, fallback to CourseKey
            try:
                course = CourseOverview.objects.get(id=course_id)
                org_name = course.org
            except CourseOverview.DoesNotExist:
                # Fallback: extract org directly from course_id
                org_name = course_id.org

            # Check if org-level ban exists
            org_ban = cls.objects.filter(
                user=user,
                org_key=org_name,
                scope=cls.SCOPE_ORGANIZATION,
                is_active=True
            ).first()

            if org_ban:
                # Check if there's an exception for this specific course
                if DiscussionBanException.objects.filter(
                    ban=org_ban,
                    course_id=course_id
                ).exists():
                    # Exception exists - user is allowed in this course
                    return False
                # Org ban applies, no exception
                return True

        # Check course-level ban
        if cls.objects.filter(
            user=user,
            course_id=course_id,
            scope=cls.SCOPE_COURSE,
            is_active=True
        ).exists():
            return True

        return False


class DiscussionBanException(TimeStampedModel):
    """
    Tracks course-level exceptions to organization-level bans.

    Allows moderators to unban a user from specific courses while
    maintaining an organization-wide ban for all other courses.

    Uses edX standard patterns:
    - TimeStampedModel for created/modified timestamps

    Example:
    - User banned from all HarvardX courses (org-level ban)
    - Exception created for HarvardX+CS50+2024
    - User can participate in CS50 but remains banned in all other HarvardX courses
    """

    # Core Fields
    ban = models.ForeignKey(
        'DiscussionBan',
        on_delete=models.CASCADE,
        related_name='exceptions',
        help_text="The organization-level ban this exception applies to"
    )
    course_id = CourseKeyField(
        max_length=255,
        db_index=True,
        help_text="Specific course where user is unbanned despite org-level ban"
    )

    # Metadata
    unbanned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ban_exceptions_created',
    )
    reason = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'discussion_ban_exception'
        constraints = [
            models.UniqueConstraint(
                fields=['ban', 'course_id'],
                name='unique_ban_exception'
            ),
        ]
        indexes = [
            models.Index(fields=['ban', 'course_id'], name='idx_ban_course'),
            models.Index(fields=['course_id'], name='idx_exception_course'),
        ]
        verbose_name = _('Discussion Ban Exception')
        verbose_name_plural = _('Discussion Ban Exceptions')

    def __str__(self):
        return f"Exception: {self.ban.user.username} allowed in {self.course_id}"

    def clean(self):
        """Validate that exception only applies to organization-level bans."""
        super().clean()
        if self.ban.scope != 'organization':
            raise ValidationError(_("Exceptions can only be created for organization-level bans"))