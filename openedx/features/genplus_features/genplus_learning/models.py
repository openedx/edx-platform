import uuid
from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError
from django_extensions.db.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField
from simple_history.models import HistoricalRecords

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore.django import modulestore
from openedx.features.genplus_features.genplus_learning.constants import ProgramEnrollmentStatuses
from openedx.features.genplus_features.genplus.models import Student, Class
from openedx.features.genplus_features.genplus_learning.utils import (get_class_unit_progress,
                                                                      get_class_lesson_progress)


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

    @property
    def display_name(self):
        return self.course.display_name

    @property
    def short_description(self):
        return self.course.short_description

    @property
    def lms_url(self):
        course = modulestore().get_course(self.course.id)
        course_key_str = str(course.id)
        sections = course.children
        if sections:
            usage_key_str = str(sections[0])
        else:
            usage_key_str = str(modulestore().make_course_usage_key(course.id))

        return f"{settings.LMS_ROOT_URL}/courses/{course_key_str}/jump_to/{usage_key_str}"

    @property
    def banner_image_url(self):
        return f"{settings.LMS_ROOT_URL}{self.course.course_image_url}"

    def is_locked(self, gen_class):
        class_unit = self.class_units.filter(gen_class=gen_class).first()
        if class_unit:
            return class_unit.is_locked
        return True

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

    program_enrollment = models.ForeignKey(ProgramEnrollment, on_delete=models.CASCADE,
                                           related_name="program_unit_enrollments")
    course_enrollment = models.ForeignKey(CourseEnrollment, null=True, blank=True, on_delete=models.CASCADE)
    course = models.ForeignKey(CourseOverview, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()


class ClassUnit(models.Model):
    class Meta:
        unique_together = ("gen_class", "unit")

    gen_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="class_units")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="class_units")

    @property
    def is_locked(self):
        return all([lesson.is_locked for lesson in self.class_lessons.all()])

    def __str__(self):
        return f"{self.gen_class.name}-{self.unit.course.display_name}"

    @property
    def class_unit_progress(self):
        return get_class_unit_progress(self.unit.course.id, self.gen_class)


class ClassLesson(models.Model):
    class Meta:
        unique_together = ("class_unit", "usage_key")

    class_unit = models.ForeignKey(ClassUnit, on_delete=models.CASCADE, related_name="class_lessons")
    course_key = CourseKeyField(max_length=255)
    usage_key = UsageKeyField(max_length=255)
    is_locked = models.BooleanField(default=True)

    @property
    def class_lesson_progress(self):
        return get_class_lesson_progress(self.usage_key, self.class_unit.gen_class)

    @property
    def lms_url(self):
        return f"{settings.LMS_ROOT_URL}/courses/{str(self.course_key)}/jump_to/{str(self.usage_key)}"
