"""
Models for the custom course feature
"""
from django.contrib.auth.models import User
from django.db import models

from student.models import CourseEnrollment, AlreadyEnrolledError  # pylint: disable=import-error
from xmodule_django.models import CourseKeyField, LocationKeyField  # pylint: disable=import-error


class CustomCourseForEdX(models.Model):
    """
    A Custom Course.
    """
    course_id = CourseKeyField(max_length=255, db_index=True)
    display_name = models.CharField(max_length=255)
    coach = models.ForeignKey(User, db_index=True)


class CcxMembership(models.Model):
    """
    Which students are in a CCX?
    """
    ccx = models.ForeignKey(CustomCourseForEdX, db_index=True)
    student = models.ForeignKey(User, db_index=True)
    active = models.BooleanField(default=False)

    @classmethod
    def auto_enroll(cls, student, future_membership):
        """convert future_membership to an active membership
        """
        if not future_membership.auto_enroll:
            msg = "auto enrollment not allowed for {}"
            raise ValueError(msg.format(future_membership))
        membership = cls(
            ccx=future_membership.ccx, student=student, active=True
        )
        try:
            CourseEnrollment.enroll(
                student, future_membership.ccx.course_id, check_access=True
            )
        except AlreadyEnrolledError:
            # if the user is already enrolled in the course, great!
            pass

        membership.save()
        future_membership.delete()

    @classmethod
    def memberships_for_user(cls, user, active=True):
        """
        active memberships for a user
        """
        return cls.objects.filter(student=user, active__exact=active)


class CcxFutureMembership(models.Model):
    """
    Which emails for non-users are waiting to be added to CCX on registration
    """
    ccx = models.ForeignKey(CustomCourseForEdX, db_index=True)
    email = models.CharField(max_length=255)
    auto_enroll = models.BooleanField(default=0)


class CcxFieldOverride(models.Model):
    """
    Field overrides for custom courses.
    """
    ccx = models.ForeignKey(CustomCourseForEdX, db_index=True)
    location = LocationKeyField(max_length=255, db_index=True)
    field = models.CharField(max_length=255)

    class Meta:  # pylint: disable=missing-docstring,old-style-class
        unique_together = (('ccx', 'location', 'field'),)

    value = models.TextField(default='null')
