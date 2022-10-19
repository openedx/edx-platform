import logging
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed, pre_save

from completion.models import BlockCompletion
from xmodule.modulestore.django import SignalHandler, modulestore
from openedx.features.genplus_features.genplus.models import Class, Teacher, Activity
from openedx.features.genplus_features.genplus.constants import ActivityTypes
import openedx.features.genplus_features.genplus_learning.tasks as genplus_learning_tasks
from openedx.features.genplus_features.genplus_learning.models import (
    Program, Unit, ClassUnit, ClassLesson , UnitBlockCompletion
)
from openedx.features.genplus_features.genplus_learning.access import allow_access
from openedx.features.genplus_features.genplus_learning.roles import ProgramInstructorRole
from openedx.features.genplus_features.genplus_learning.utils import update_class_lessons
log = logging.getLogger(__name__)


def _create_class_unit_and_lessons(gen_class):
    # create class_units and class_lessons for units in this program
    units = gen_class.program.units.all()
    class_lessons = []
    for unit in units:
        class_unit, created = ClassUnit.objects.get_or_create(gen_class=gen_class, unit=unit, course_key=unit.course.id)
        course = modulestore().get_course(class_unit.course_key)
        lessons = course.children
        class_lessons += [
            ClassLesson(order=order, class_unit=class_unit,
                        course_key=class_unit.course_key, usage_key=usage_key)
            for order, usage_key in enumerate(lessons, start=1)
        ]

    ClassLesson.objects.bulk_create(class_lessons, ignore_conflicts=True)


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):
    update_class_lessons(course_key)


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

        _create_class_unit_and_lessons(instance)


# TODO : modification required after m2m relation change
# @receiver(m2m_changed, sender=Class.students.through)
# def class_students_changed(sender, instance, action, **kwargs):
#     pk_set = kwargs.pop('pk_set', None)
#     if action == "post_add":
#         if isinstance(instance, Class) and instance.program:
#             genplus_learning_tasks.enroll_class_students_to_program.apply_async(
#                 args=[instance.pk, instance.program.pk],
#                 kwargs={
#                     'class_student_ids': list(pk_set),
#                 },
#                 countdown=settings.PROGRAM_ENROLLMENT_COUNTDOWN
#             )


@receiver(post_save, sender=BlockCompletion)
def set_unit_and_block_completions(sender, instance, created, **kwargs):
    if created:
        genplus_learning_tasks.update_unit_and_lesson_completions.apply_async(
            args=[instance.pk]
        )


# capture activity on lesson completion
@receiver(post_save, sender=UnitBlockCompletion)
def create_activity_on_lesson_completion(sender, instance, created, **kwargs):
    if instance.is_complete:
        Activity.objects.create(
            actor=instance.user.gen_user.student,
            type=ActivityTypes.LESSON_COMPLETION,
            action_object=instance,
            target=instance.user.gen_user.student
        )
