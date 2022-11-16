import uuid

from django.conf import settings
from django.db import models
from slugify import slugify
from django.core.exceptions import ValidationError
from django_extensions.db.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField
from simple_history.models import HistoricalRecords

from openedx.core.djangoapps.signals.signals import COURSE_COMPLETED
from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore.django import modulestore
from openedx.features.genplus_features.genplus_learning.constants import ProgramEnrollmentStatuses, ProgramStatuses
from openedx.features.genplus_features.genplus.models import Student, Class, Skill

USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


def validate_percent(value):
    if (value is None) or (not 0 <= value <= 100):
        raise ValidationError(_('{value} must be between 0 and 100').format(value=value))


class YearGroup(models.Model):
    name = models.CharField(max_length=128, unique=True)
    program_name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Program(TimeStampedModel):
    STATUS_CHOICES = ProgramStatuses.__MODEL_CHOICES__

    uuid = models.UUIDField(default=uuid.uuid4)
    slug = models.SlugField(max_length=64, unique=True, blank=True)
    year_group = models.ForeignKey(YearGroup, on_delete=models.CASCADE, related_name='programs')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=ProgramStatuses.UNPUBLISHED)
    banner_image = models.ImageField(upload_to="program_banner_images", default="")
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(
                "{} {} {} {}".format(
                    self.year_group.name,
                    self.year_group.program_name,
                    self.start_date.year,
                    self.end_date.year,
                ), separator="_"
            )
        super(Program, self).save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status == ProgramStatuses.ACTIVE

    @property
    def is_unpublished(self):
        return self.status == ProgramStatuses.UNPUBLISHED

    @classmethod
    def get_active_programs(cls):
        return cls.objects.filter(status=ProgramStatuses.ACTIVE)

    def __str__(self):
        return self.year_group.name


class Unit(models.Model):
    order = models.PositiveIntegerField(default=0, blank=False, null=False)
    course = models.OneToOneField(CourseOverview, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="units")
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True)
    unit_image = models.ImageField(upload_to="unit_images", blank=True, default="")

    class Meta:
        ordering = ['order']

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
    gen_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name="program_enrollments")
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
        unique_together = ("gen_class", "unit",)
        ordering = ["unit__order"]

    gen_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="class_units")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="class_units")
    course_key = CourseKeyField(max_length=255)

    @property
    def is_locked(self):
        return all([lesson.is_locked for lesson in self.class_lessons.all()])

    def __str__(self):
        return f"{self.gen_class.name}-{self.unit.course.display_name}"


class ClassLesson(models.Model):
    class Meta:
        unique_together = ("class_unit", "usage_key",)
        ordering = ["order"]

    class_unit = models.ForeignKey(ClassUnit, on_delete=models.CASCADE, related_name="class_lessons")
    order = models.PositiveIntegerField(default=0, blank=False, null=False)
    course_key = CourseKeyField(max_length=255)
    usage_key = UsageKeyField(max_length=255)
    is_locked = models.BooleanField(default=True)

    @property
    def display_name(self):
        return modulestore().get_item(self.usage_key).display_name

    @property
    def lms_url(self):
        return f"{settings.LMS_ROOT_URL}/courses/{str(self.course_key)}/jump_to/{str(self.usage_key)}"


class UnitCompletion(models.Model):
    class Meta:
        unique_together = ('user', 'course_key',)

    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    course_key = CourseKeyField(max_length=255, db_index=True)
    is_complete = models.BooleanField(default=False)
    completion_date = models.DateTimeField(blank=True, null=True)
    progress = models.FloatField(validators=[validate_percent])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_complete:
            COURSE_COMPLETED.send_robust(
                sender=self.__class__,
                user=self.user,
                course_key=self.course_key
            )


class UnitBlockCompletion(models.Model):
    class Meta:
        unique_together = ('user', 'course_key', 'usage_key',)

    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    course_key = CourseKeyField(max_length=255, db_index=True)
    usage_key = UsageKeyField(max_length=255, db_index=True)
    block_type = models.CharField(max_length=64)
    is_complete = models.BooleanField(default=False)
    completion_date = models.DateTimeField(blank=True, null=True)
    progress = models.FloatField(validators=[validate_percent])

    @property
    def lesson_name(self):
        return modulestore().get_item(self.usage_key).display_name

    @property
    def course_name(self):
        return modulestore().get_course(self.course_key).display_name
