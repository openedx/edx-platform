"""
Management command to remove enrollments and any related models created as
a side effect of enrolling students.

Intented for use in integration sandbox environments
"""
from __future__ import absolute_import

import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment, ProgramEnrollment
from student.models import CourseEnrollment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Deletes all enrollments and related data

    Example usage:
        $ ./manage.py lms reset_enrollment_data
    """

    @transaction.atomic
    def handle(self, *args, **options):
        CourseEnrollment.objects.all().delete()
        ProgramEnrollment.objects.all().delete()
        ProgramCourseEnrollment.objects.all().delete()
