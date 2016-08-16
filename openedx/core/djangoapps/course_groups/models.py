"""
Django models related to course groups functionality.
"""

import json
import logging

from django.contrib.auth.models import User
from django.db import models, transaction
from util.db import outer_atomic
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from xmodule_django.models import CourseKeyField

log = logging.getLogger(__name__)


class CourseUserGroup(models.Model):
    """
    This model represents groups of users in a course.  Groups may have different types,
    which may be treated specially.  For example, a user can be in at most one cohort per
    course, and cohorts are used to split up the forums by group.
    """
    class Meta(object):
        unique_together = (('name', 'course_id'), )

    name = models.CharField(max_length=255,
                            help_text=("What is the name of this group?  "
                                       "Must be unique within a course."))
    users = models.ManyToManyField(User, db_index=True, related_name='course_groups',
                                   help_text="Who is in this group?")

    # Note: groups associated with particular runs of a course.  E.g. Fall 2012 and Spring
    # 2013 versions of 6.00x will have separate groups.
    course_id = CourseKeyField(
        max_length=255,
        db_index=True,
        help_text="Which course is this group associated with?",
    )

    # For now, only have group type 'cohort', but adding a type field to support
    # things like 'question_discussion', 'friends', 'off-line-class', etc
    COHORT = 'cohort'  # If changing this string, update it in migration 0006.forwards() as well
    GROUP_TYPE_CHOICES = ((COHORT, 'Cohort'),)
    group_type = models.CharField(max_length=20, choices=GROUP_TYPE_CHOICES)

    @classmethod
    def create(cls, name, course_id, group_type=COHORT):
        """
        Create a new course user group.

        Args:
            name: Name of group
            course_id: course id
            group_type: group type
        """
        return cls.objects.get_or_create(
            course_id=course_id,
            group_type=group_type,
            name=name
        )


class CohortMembership(models.Model):
    """Used internally to enforce our particular definition of uniqueness"""

    course_user_group = models.ForeignKey(CourseUserGroup)
    user = models.ForeignKey(User)
    course_id = CourseKeyField(max_length=255)

    previous_cohort = None
    previous_cohort_name = None
    previous_cohort_id = None

    class Meta(object):
        unique_together = (('user', 'course_id'), )

    def clean_fields(self, *args, **kwargs):
        if self.course_id is None:
            self.course_id = self.course_user_group.course_id
        super(CohortMembership, self).clean_fields(*args, **kwargs)

    def clean(self):
        if self.course_user_group.group_type != CourseUserGroup.COHORT:
            raise ValidationError("CohortMembership cannot be used with CourseGroup types other than COHORT")
        if self.course_user_group.course_id != self.course_id:
            raise ValidationError("Non-matching course_ids provided")

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False)

        log.info("Saving CohortMembership for user '%s' in '%s'", self.user.id, self.course_id)

        # Avoid infinite recursion if creating from get_or_create() call below.
        # This block also allows middleware to use CohortMembership.get_or_create without worrying about outer_atomic
        if 'force_insert' in kwargs and kwargs['force_insert'] is True:
            with transaction.atomic():
                self.course_user_group.users.add(self.user)
                super(CohortMembership, self).save(*args, **kwargs)
            return

        # This block will transactionally commit updates to CohortMembership and underlying course_user_groups.
        # Note the use of outer_atomic, which guarantees that operations are committed to the database on block exit.
        # If called from a view method, that method must be marked with @transaction.non_atomic_requests.
        with outer_atomic(read_committed=True):

            saved_membership, created = CohortMembership.objects.select_for_update().get_or_create(
                user__id=self.user.id,
                course_id=self.course_id,
                defaults={
                    'course_user_group': self.course_user_group,
                    'user': self.user
                }
            )

            # If the membership was newly created, all the validation and course_user_group logic was settled
            # with a call to self.save(force_insert=True), which gets handled above.
            if created:
                return

            if saved_membership.course_user_group == self.course_user_group:
                raise ValueError("User {user_name} already present in cohort {cohort_name}".format(
                    user_name=self.user.username,
                    cohort_name=self.course_user_group.name
                ))
            self.previous_cohort = saved_membership.course_user_group
            self.previous_cohort_name = saved_membership.course_user_group.name
            self.previous_cohort_id = saved_membership.course_user_group.id
            self.previous_cohort.users.remove(self.user)

            saved_membership.course_user_group = self.course_user_group
            self.course_user_group.users.add(self.user)

            super(CohortMembership, saved_membership).save(update_fields=['course_user_group'])


# Needs to exist outside class definition in order to use 'sender=CohortMembership'
@receiver(pre_delete, sender=CohortMembership)
def remove_user_from_cohort(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Ensures that when a CohortMemebrship is deleted, the underlying CourseUserGroup
    has its users list updated to reflect the change as well.
    """
    instance.course_user_group.users.remove(instance.user)
    instance.course_user_group.save()


class CourseUserGroupPartitionGroup(models.Model):
    """
    Create User Partition Info.
    """
    course_user_group = models.OneToOneField(CourseUserGroup)
    partition_id = models.IntegerField(
        help_text="contains the id of a cohorted partition in this course"
    )
    group_id = models.IntegerField(
        help_text="contains the id of a specific group within the cohorted partition"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CourseCohortsSettings(models.Model):
    """
    This model represents cohort settings for courses.
    """
    is_cohorted = models.BooleanField(default=False)

    course_id = CourseKeyField(
        unique=True,
        max_length=255,
        db_index=True,
        help_text="Which course are these settings associated with?",
    )

    _cohorted_discussions = models.TextField(db_column='cohorted_discussions', null=True, blank=True)  # JSON list

    # pylint: disable=invalid-name
    always_cohort_inline_discussions = models.BooleanField(default=True)

    @property
    def cohorted_discussions(self):
        """Jsonify the cohorted_discussions"""
        return json.loads(self._cohorted_discussions)

    @cohorted_discussions.setter
    def cohorted_discussions(self, value):
        """Un-Jsonify the cohorted_discussions"""
        self._cohorted_discussions = json.dumps(value)


class CourseCohort(models.Model):
    """
    This model represents cohort related info.
    """
    course_user_group = models.OneToOneField(CourseUserGroup, unique=True, related_name='cohort')

    RANDOM = 'random'
    MANUAL = 'manual'
    ASSIGNMENT_TYPE_CHOICES = ((RANDOM, 'Random'), (MANUAL, 'Manual'),)
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPE_CHOICES, default=MANUAL)

    @classmethod
    def create(cls, cohort_name=None, course_id=None, course_user_group=None, assignment_type=MANUAL):
        """
        Create a complete(CourseUserGroup + CourseCohort) object.

        Args:
            cohort_name: Name of the cohort to be created
            course_id: Course Id
            course_user_group: CourseUserGroup
            assignment_type: 'random' or 'manual'
        """
        if course_user_group is None:
            course_user_group, __ = CourseUserGroup.create(cohort_name, course_id)

        course_cohort, __ = cls.objects.get_or_create(
            course_user_group=course_user_group,
            defaults={'assignment_type': assignment_type}
        )

        return course_cohort
