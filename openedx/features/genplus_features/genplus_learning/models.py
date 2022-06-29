import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django_extensions.db.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField
from simple_history.models import HistoricalRecords

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from .utils import get_section_completion_percentage
from .constants import ProgramEnrollmentStatuses
from openedx.features.genplus_features.genplus.models import Student, Class


class YearGroup(models.Model):
    name = models.CharField(max_length=128, unique=True)
    program_name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Program(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4)
    year_group = models.ForeignKey(
        YearGroup,
        on_delete=models.CASCADE,
        related_name='programs'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    units = models.ManyToManyField(
        CourseOverview,
        related_name='programs',
        blank=True
    )
    history = HistoricalRecords()

    @classmethod
    def get_current_programs(cls):
        return cls.objects.filter(is_current=True)

    def __str__(self):
        return self.year_group.name


class ClassEnrollment(models.Model):
    class Meta:
        unique_together = ('gen_class', 'program',)

    gen_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="class_enrollments")
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="class_enrollments")
    history = HistoricalRecords()


class ProgramEnrollment(TimeStampedModel):
    STATUS_CHOICES = ProgramEnrollmentStatuses.__MODEL_CHOICES__

    class Meta:
        unique_together = ('student', 'from_class', 'program',)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="program_enrollments",
    )
    from_class = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="program_enrollments",
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="program_enrollments",
    )
    status = models.CharField(max_length=9, choices=STATUS_CHOICES)
    history = HistoricalRecords()


class ProgramUnitEnrollment(TimeStampedModel):
    class Meta:
        unique_together = ('program_enrollment', 'course_key',)

    program_enrollment = models.ForeignKey(
        ProgramEnrollment,
        on_delete=models.CASCADE,
        related_name="program_unit_enrollments",
    )
    course_enrollment = models.ForeignKey(
        CourseEnrollment,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    course_key = CourseKeyField(max_length=255)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()


class Lesson(models.Model):
    class Meta:
        unique_together = ("course_key", "usage_key")

    course_key = CourseKeyField(max_length=255)
    usage_key = UsageKeyField(max_length=255)
    is_locked = models.BooleanField(default=True)

    def get_user_progress(self, user):
        return get_section_completion_percentage(self.usage_key, user)
