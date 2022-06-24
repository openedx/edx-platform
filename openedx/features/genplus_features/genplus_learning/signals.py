import logging

from django.dispatch import receiver
from xmodule.modulestore.django import SignalHandler, modulestore
from django.db.models.signals import post_save

from .models import Lesson, ClassEnrollment, ProgramEnrollment
from .constants import ProgramEnrollmentStatuses
import openedx.features.genplus_features.genplus_learning.tasks as genplus_learning_tasks

log = logging.getLogger(__name__)


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):
    course = modulestore().get_course(course_key)
    section_usage_keys = set(course.children)
    for usage_key in section_usage_keys:
        Lesson.objects.get_or_create(course_key=course_key, usage_key=usage_key)

    lessons = Lesson.objects.filter(course_key=course_key)
    lesson_usage_keys = set(lessons.values_list('usage_key', flat=True))
    for usage_key in (lesson_usage_keys - section_usage_keys):
        Lesson.objects.get(course_key=course_key, usage_key=usage_key).delete()


@receiver(post_save, sender=ClassEnrollment)
def add_program_enrollment(sender, instance, created, **kwargs):
    if created:
        genplus_learning_tasks.enroll_class_students_to_program.delay(
            gen_class_id=instance.gen_class.pk,
            program_id=instance.program.pk,
        )
