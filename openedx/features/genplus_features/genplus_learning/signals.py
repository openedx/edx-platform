import logging

from django.dispatch import receiver
from xmodule.modulestore.django import SignalHandler, modulestore
from django.db.models.signals import post_save, m2m_changed

from openedx.features.genplus_features.genplus.models import Class
from .models import Lesson, ClassEnrollment, Program
from .constants import ProgramEnrollmentStatuses
import openedx.features.genplus_features.genplus_learning.tasks as genplus_learning_tasks

log = logging.getLogger(__name__)

PROGRAM_ENROLLMENT_COUNTDOWN = 10


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
        genplus_learning_tasks.enroll_class_students_to_program.apply_async(
            args=[instance.gen_class.pk, instance.program.pk],
            countdown=PROGRAM_ENROLLMENT_COUNTDOWN,
        )


@receiver(m2m_changed, sender=Program.units.through)
def program_units_changed(sender, instance, action, **kwargs):
    pk_set = kwargs.pop('pk_set', None)
    if action == "post_add":
        if isinstance(instance, Program) and instance.is_current:
            program_class_ids = instance.class_enrollments.all().values_list('gen_class', flat=True)
            program_unit_ids = [str(course_key) for course_key in pk_set]
            for class_id in program_class_ids:
                genplus_learning_tasks.enroll_class_students_to_program.apply_async(
                    args=[class_id, instance.pk],
                    kwargs={
                        'program_unit_ids': program_unit_ids
                    },
                    countdown=PROGRAM_ENROLLMENT_COUNTDOWN
                )


@receiver(m2m_changed, sender=Class.students.through)
def class_students_changed(sender, instance, action, **kwargs):
    pk_set = kwargs.pop('pk_set', None)
    if action == "post_add":
        current_program = instance.current_program
        if isinstance(instance, Class) and current_program:
            genplus_learning_tasks.enroll_class_students_to_program.apply_async(
                args=[instance.pk, current_program.pk],
                kwargs={
                    'class_student_ids': list(pk_set),
                },
                countdown=PROGRAM_ENROLLMENT_COUNTDOWN
            )
