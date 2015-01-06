from django.contrib.auth.models import User
from django.db import models

from student.models import CourseEnrollment, AlreadyEnrolledError
from xmodule_django.models import CourseKeyField, LocationKeyField


class PersonalOnlineCourse(models.Model):
    """
    A Personal Online Course.
    """
    course_id = CourseKeyField(max_length=255, db_index=True)
    display_name = models.CharField(max_length=255)
    coach = models.ForeignKey(User, db_index=True)


class PocMembership(models.Model):
    """
    Which students are in a POC?
    """
    poc = models.ForeignKey(PersonalOnlineCourse, db_index=True)
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
            poc=future_membership.poc, student=student, active=True
        )
        try:
            CourseEnrollment.enroll(
                student, future_membership.poc.course_id, check_access=True
            )
        except AlreadyEnrolledError:
            # if the user is already enrolled in the course, great!
            pass

        membership.save()
        future_membership.delete()

    @classmethod
    def memberships_for_user(cls, user, active=True):
        return cls.objects.filter(student=user, active__exact=active)


class PocFutureMembership(models.Model):
    """
    Which emails for non-users are waiting to be added to POC on registration
    """
    poc = models.ForeignKey(PersonalOnlineCourse, db_index=True)
    email = models.CharField(max_length=255)
    auto_enroll = models.BooleanField(default=0)


class PocFieldOverride(models.Model):
    """
    Field overrides for personal online courses.
    """
    poc = models.ForeignKey(PersonalOnlineCourse, db_index=True)
    location = LocationKeyField(max_length=255, db_index=True)
    field = models.CharField(max_length=255)

    class Meta:
        unique_together = (('poc', 'location', 'field'),)

    value = models.TextField(default='null')
