import uuid
from django.db import models
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from django_extensions.db.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField
from simple_history.models import HistoricalRecords

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from .utils import get_section_progress
from .constants import ProgramEnrollmentStatuses
from openedx.features.genplus_features.genplus.models import Student, Class


class YearGroup(models.Model):
    name = models.CharField(max_length=128, unique=True)
    program_name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Program(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4)
    slug = models.SlugField(max_length=64, unique=True)
    year_group = models.ForeignKey(YearGroup, on_delete=models.CASCADE, related_name='programs')
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        self.slug = slugify(
            "{} {} {}".format(
                self.year_group.name,
                self.start_date.year,
                self.end_date.year,
            )
        )
        super(Program, self).save(*args, **kwargs)


    @classmethod
    def get_current_programs(cls):
        return cls.objects.filter(is_current=True)

    def __str__(self):
        return self.year_group.name


class Unit(models.Model):
    course = models.OneToOneField(CourseOverview, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="units")

    def __str__(self):
        return str(self.course.id)


class ProgramEnrollment(TimeStampedModel):
    STATUS_CHOICES = ProgramEnrollmentStatuses.__MODEL_CHOICES__

    class Meta:
        unique_together = ('student', 'program',)

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="program_enrollments")
    gen_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="program_enrollments")
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="program_enrollments")
    status = models.CharField(max_length=9, choices=STATUS_CHOICES)
    history = HistoricalRecords()


class ProgramUnitEnrollment(TimeStampedModel):
    class Meta:
        unique_together = ('program_enrollment', 'course',)

    program_enrollment = models.ForeignKey(ProgramEnrollment, on_delete=models.CASCADE, related_name="program_unit_enrollments")
    course_enrollment = models.ForeignKey(CourseEnrollment, null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey(CourseOverview, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()


class ClassUnit(models.Model):
    class Meta:
        unique_together = ("gen_class", "unit")

    gen_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="class_units")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="class_units")

    def __str__(self):
        return f"{self.gen_class.name}-{self.unit.course.display_name}"


class ClassLesson(models.Model):
    class Meta:
        unique_together = ("class_unit", "usage_key")

    class_unit = models.ForeignKey(ClassUnit, on_delete=models.CASCADE, related_name="class_lessons")
    course_key = CourseKeyField(max_length=255)
    usage_key = UsageKeyField(max_length=255)
    is_locked = models.BooleanField(default=True)
