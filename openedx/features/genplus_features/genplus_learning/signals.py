import logging

from django.conf import settings
from django.dispatch import receiver
from xmodule.modulestore.django import SignalHandler, modulestore
from django.db.models.signals import post_save, m2m_changed, pre_save

from openedx.features.genplus_features.genplus.models import Class, Teacher
from .models import ClassLesson, Program, Unit, ClassUnit
from .constants import ProgramEnrollmentStatuses
import openedx.features.genplus_features.genplus_learning.tasks as genplus_learning_tasks
from openedx.features.genplus_features.genplus_learning.access import allow_access
from openedx.features.genplus_features.genplus_learning.roles import ProgramInstructorRole

log = logging.getLogger(__name__)


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):
    # retrieve units for all classes with course_key
    class_units = ClassUnit.objects.filter(unit__course__id=course_key)

    course = modulestore().get_course(course_key)
    new_lesson_usage_keys = set(course.children) # children has list of section usage keys

    old_lessons = ClassLesson.objects.filter(course_key=course_key)
    old_lesson_usage_keys = set(old_lessons.values_list('usage_key', flat=True))

    removed_usage_keys = old_lesson_usage_keys - new_lesson_usage_keys
    # delete removed section_usage_keys records
    ClassLesson.objects.filter(course_key=course_key, usage_key__in=removed_usage_keys).delete()

    new_usage_keys = new_lesson_usage_keys - old_lesson_usage_keys

    new_class_lessons = [
        ClassLesson(class_unit=class_unit, course_key=course_key, usage_key=usage_key)
        for class_unit in class_units
        for usage_key in new_usage_keys
    ]

    # bulk create new class lessons
    ClassLesson.objects.bulk_create(new_class_lessons)


@receiver(pre_save, sender=Class)
def gen_class_changed(sender, instance, *args, **kwargs):
    gen_class_qs = Class.objects.filter(pk=instance.pk)
    if gen_class_qs.exists() and gen_class_qs.first().program:
        return

    if instance.program:
        # enroll students to the program
        genplus_learning_tasks.enroll_class_students_to_program.apply_async(
            args=[instance.pk, instance.program.pk],
            countdown=settings.PROGRAM_ENROLLMENT_COUNTDOWN,
        )

        # give staff access to teachers
        for teacher in instance.teachers.all():
            allow_access(instance.program, teacher.gen_user, ProgramInstructorRole.ROLE_NAME)

        # create class_units for units in this program
        class_units = [
            ClassUnit(gen_class=instance, unit=unit)
            for unit in instance.program.units.all()
        ]
        ClassUnit.objects.bulk_create(class_units)


@receiver(post_save, sender=Unit)
def program_unit_added(sender, instance, created, **kwargs):
    if created and instance.program:
        program_class_ids = instance.program.classes.all().values_list('pk', flat=True)
        for class_id in program_class_ids:
            genplus_learning_tasks.enroll_class_students_to_program.apply_async(
                args=[class_id, instance.program.pk],
                kwargs={
                    'program_unit_ids': [str(unit.course.id)]
                },
                countdown=settings.PROGRAM_ENROLLMENT_COUNTDOWN
            )


@receiver(m2m_changed, sender=Class.students.through)
def class_students_changed(sender, instance, action, **kwargs):
    pk_set = kwargs.pop('pk_set', None)
    if action == "post_add":
        if isinstance(instance, Class) and instance.program:
            genplus_learning_tasks.enroll_class_students_to_program.apply_async(
                args=[instance.pk, instance.program.pk],
                kwargs={
                    'class_student_ids': list(pk_set),
                },
                countdown=settings.PROGRAM_ENROLLMENT_COUNTDOWN
            )
