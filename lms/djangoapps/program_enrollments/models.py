# -*- coding: utf-8 -*-
"""
Django model specifications for the Program Enrollments API
"""
from __future__ import unicode_literals
import logging

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from lms.djangoapps.program_enrollments.api.v1.constants import (
    CourseEnrollmentResponseStatuses as ProgramCourseEnrollmentResponseStatuses
)
from openedx.core.djangoapps.course_modes.models import CourseMode
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField
from simple_history.models import HistoricalRecords
from student.models import AlreadyEnrolledError, CourseEnrollment

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class ProgramEnrollment(TimeStampedModel):  # pylint: disable=model-missing-unicode
    """
    This is a model for Program Enrollments from the registrar service

    .. pii: PII is found in the external key for a program enrollment
    .. pii_types: other
    .. pii_retirement: local_api
    """
    STATUSES = (
        ('enrolled', 'enrolled'),
        ('pending', 'pending'),
        ('suspended', 'suspended'),
        ('withdrawn', 'withdrawn'),
    )

    class Meta(object):
        app_label = "program_enrollments"
        unique_together = ('external_user_key', 'program_uuid', 'curriculum_uuid')

        # A student enrolled in a given (program, curriculum) should always
        # have a non-null ``user`` or ``external_user_key`` field (or both).
        unique_together = (
            ('user', 'external_user_key', 'program_uuid', 'curriculum_uuid'),
        )

    user = models.ForeignKey(
        User,
        null=True,
        blank=True
    )
    external_user_key = models.CharField(
        db_index=True,
        max_length=255,
        null=True
    )
    program_uuid = models.UUIDField(db_index=True, null=False)
    curriculum_uuid = models.UUIDField(db_index=True, null=False)
    status = models.CharField(max_length=9, choices=STATUSES)
    historical_records = HistoricalRecords()

    def clean(self):
        if not (self.user or self.external_user_key):
            raise ValidationError(_('One of user or external_user_key must not be null.'))

    @classmethod
    def bulk_read_by_student_key(cls, program_uuid, student_data):
        """
        args:
            program_uuid - The UUID of the program to read enrollment data of.
            student_data - A dictionary keyed by external_user_key and
            valued by a dict containing the curriculum_uuid for the user in the given program.
        """
        return cls.objects.filter(
            program_uuid=program_uuid,
            external_user_key__in=student_data.keys(),
        )

    @classmethod
    def retire_user(cls, user_id):
        """
        With the parameter user_id, retire the external_user_key field

        Return True if there is data that was retired
        Return False if there is no matching data
        """

        enrollments = cls.objects.filter(user=user_id)
        if not enrollments:
            return False

        for enrollment in enrollments:
            enrollment.historical_records.update(external_user_key=None)

        enrollments.update(external_user_key=None)
        return True

    def get_program_course_enrollment(self, course_key):
        """
        Returns the ProgramCourseEnrollment associated with this ProgramEnrollment and given course,
         None if it does not exist
        """
        try:
            program_course_enrollment = self.program_course_enrollments.get(course_key=course_key)
        except ProgramCourseEnrollment.DoesNotExist:
            return None
        return program_course_enrollment

    def __str__(self):
        return '[ProgramEnrollment id={}]'.format(self.id)


class ProgramCourseEnrollment(TimeStampedModel):  # pylint: disable=model-missing-unicode
    """
    This is a model to represent a learner's enrollment in a course
    in the context of a program from the registrar service

    .. no_pii:
    """
    STATUSES = (
        ('active', 'active'),
        ('inactive', 'inactive'),
    )

    class Meta(object):
        app_label = "program_enrollments"

    program_enrollment = models.ForeignKey(
        ProgramEnrollment,
        on_delete=models.CASCADE,
        related_name="program_course_enrollments"
    )
    course_enrollment = models.OneToOneField(
        CourseEnrollment,
        null=True,
        blank=True,
    )
    course_key = CourseKeyField(max_length=255)
    status = models.CharField(max_length=9, choices=STATUSES)
    historical_records = HistoricalRecords()

    def __str__(self):
        return '[ProgramCourseEnrollment id={}]'.format(self.id)

    @classmethod
    def create_program_course_enrollment(cls, program_enrollment, course_key, status):
        """
        Create ProgramCourseEnrollment for the given course and program enrollment
        """
        program_course_enrollment = ProgramCourseEnrollment.objects.create(
            program_enrollment=program_enrollment,
            course_key=course_key,
            status=status,
        )

        if program_enrollment.user:
            program_course_enrollment.enroll(program_enrollment.user)

        return program_course_enrollment.status

    def change_status(self, status):
        """
        Modify ProgramCourseEnrollment status and course_enrollment status if it exists
        """
        if status == self.status:
            return status

        self.status = status
        if self.course_enrollment:
            if status == ProgramCourseEnrollmentResponseStatuses.ACTIVE:
                self.course_enrollment.activate()
            elif status == ProgramCourseEnrollmentResponseStatuses.INACTIVE:
                self.course_enrollment.deactivate()
            else:
                message = ("Changed {enrollment} status to {status}, not changing course_enrollment"
                           " status because status is not '{active}' or '{inactive}'")
                logger.warn(message.format(
                    enrollment=self,
                    status=status,
                    active=ProgramCourseEnrollmentResponseStatuses.ACTIVE,
                    inactive=ProgramCourseEnrollmentResponseStatuses.INACTIVE
                ))
        elif self.program_enrollment.user:
            logger.warn("User {user} {program_enrollment} {course_key} has no course_enrollment".format(
                user=self.program_enrollment.user,
                program_enrollment=self.program_enrollment,
                course_key=self.course_key,
            ))
        self.save()
        return self.status

    def enroll(self, user):
        """
        Create a CourseEnrollment to enroll user in course
        """
        try:
            self.course_enrollment = CourseEnrollment.enroll(
                user,
                self.course_key,
                mode=CourseMode.MASTERS,
                check_access=True,
            )
        except AlreadyEnrolledError:
            course_enrollment = CourseEnrollment.objects.get(
                user=user,
                course_id=self.course_key,
            )
            if course_enrollment.mode == CourseMode.AUDIT or course_enrollment.mode == CourseMode.HONOR:
                course_enrollment.mode = CourseMode.MASTERS
                course_enrollment.save()
            self.course_enrollment = course_enrollment
            message = ("Attempted to create course enrollment for user={user} and course={course}"
                       " but an enrollment already exists. Existing enrollment will be used instead")
            logger.info(message.format(user=user.id, course=self.course_key))
        if self.status == ProgramCourseEnrollmentResponseStatuses.INACTIVE:
            self.course_enrollment.deactivate()
        self.save()
