"""
Django models related to course groups functionality.
"""

import json
import logging

from django.contrib.auth.models import User
from django.db import models, transaction, IntegrityError
from django.core.exceptions import ValidationError
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
    INTERNAL_NAME = '_db_internal_'

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
    COHORT = 'cohort'
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

    class Meta(object):
        unique_together = (('user', 'course_id'), )

    #the sole purpose of overriding this method is to get the django 1.6 behavior of allowing 'validate_unique'
    #for django 1.8 upgrade, just remove this method and allow the base method to be called instead.
    #reference: https://docs.djangoproject.com/en/1.6/ref/models/instances/, under "Validating Objects"
    def full_clean(self, *args, **kwargs):
        self.clean_fields()
        self.clean()
        if not 'validate_unique' in kwargs or kwargs['validate_unique'] == True:
            self.validate_unique()

    def clean_fields(self, *args, **kwargs):
        if self.course_id == None:
            self.course_id = self.course_user_group.course_id
        super(CohortMembership, self).clean_fields(*args, **kwargs)

    def clean(self):
        if self.course_user_group.group_type != CourseUserGroup.COHORT:
            raise ValidationError("CohortMembership cannot be used with CourseGroup types other than COHORT")
        if self.course_user_group.course_id != self.course_id:
            raise ValidationError("Non-matching course_ids provided")

    def save(self, *args, **kwargs):
        self.full_clean(validate_unique=False)
        if self.course_user_group.name == CourseUserGroup.INTERNAL_NAME:
            super(CohortMembership, self).save(*args, **kwargs)
            return

        self.trying_to_save = True
        while(self.trying_to_save):
            try:
                #the following 2 "transaction" lines force a fresh read, they can be removed once we're on django 1.8
                #see http://stackoverflow.com/questions/3346124/how-do-i-force-django-to-ignore-any-caches-and-reload-data
                with transaction.commit_manually():
                    transaction.commit()

                saved_membership = CohortMembership.objects.get(
                    user__id = self.user.id,
                    course_id = self.course_id,
                )
            except CohortMembership.DoesNotExist:
                try:
                    dummy_group, created  = CourseUserGroup.objects.get_or_create(
                        name=CourseUserGroup.INTERNAL_NAME,
                        course_id=self.course_user_group.course_id,
                        group_type=CourseUserGroup.COHORT
                    )
                    new_membership = CohortMembership(
                        user = self.user,
                        course_user_group = dummy_group,
                        version = 1
                    )
                    new_membership.save()
                except IntegrityError:
                    pass
                continue

            if saved_membership.course_user_group == self.course_user_group:
                raise ValueError("User {user_name} already present in cohort {cohort_name}".format(
                    user_name=self.user.username,
                    cohort_name=self.course_user_group.name
                ))
            self.previous_cohort = saved_membership.course_user_group
            if self.previous_cohort.name != CourseUserGroup.INTERNAL_NAME:
                self.previous_cohort_name = saved_membership.course_user_group.name
                self.previous_cohort_id = saved_membership.course_user_group.id

            try:
                with transaction.commit_on_success():
                    self.previous_cohort.users.remove(self.user)
                    self.course_user_group.users.add(self.user)
                    self.user.course_groups.remove(self.previous_cohort)
                    self.user.course_groups.add(self.course_user_group)
                    updated = CohortMembership.objects.filter(
                        id = saved_membership.id,
                        version = saved_membership.version
                    ).update(
                        course_user_group = self.course_user_group,
                        version = saved_membership.version + 1
                    )
                    if not updated:
                        raise IntegrityError("value of saved_membership has changed since read")
            except IntegrityError:
                continue

            self.trying_to_save = False

    course_user_group = models.ForeignKey(CourseUserGroup)
    user = models.ForeignKey(User)
    version = models.IntegerField(default=0)
    course_id = CourseKeyField(max_length=255)

    previous_cohort = None
    previous_cohort_name = None
    previous_cohort_id = None


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
