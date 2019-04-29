# -*- coding: utf-8 -*-
"""
Django model specifications for the Program Enrollments API
"""
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField
from simple_history.models import HistoricalRecords
from student.models import CourseEnrollment as StudentCourseEnrollment


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

    program_enrollment = models.ForeignKey(ProgramEnrollment, on_delete=models.CASCADE)
    course_enrollment = models.OneToOneField(
        StudentCourseEnrollment,
        null=True,
        blank=True,
    )
    course_key = CourseKeyField(max_length=255)
    status = models.CharField(max_length=9, choices=STATUSES)
    historical_records = HistoricalRecords()

    def __str__(self):
        return '[ProgramCourseEnrollment id={}]'.format(self.id)
