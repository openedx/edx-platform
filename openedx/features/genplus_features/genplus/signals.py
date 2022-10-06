from django.dispatch import receiver
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from .models import GenUser, Student, Teacher, TempUser, Class, JournalPost, Activity
from .constants import JournalTypes, ActivityTypes
USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


@receiver(post_save, sender=USER_MODEL)
def delete_temp_user(sender, instance, created, **kwargs):
    if created:
        TempUser.objects.filter(username=instance.username).delete()


@receiver(post_save, sender=GenUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_student:
            Student.objects.create(gen_user=instance)
        elif instance.is_teacher:
            Teacher.objects.create(gen_user=instance)


@receiver(post_save, sender=Teacher)
def create_teacher(sender, instance, created, **kwargs):
    classes = Class.objects.filter(school=instance.gen_user.school)
    instance.classes.add(*classes)


@receiver(post_save, sender=Class)
def create_gen_class(sender, instance, created, **kwargs):
    teachers = Teacher.objects.filter(gen_user__school=instance.school)
    instance.teachers.add(*teachers)


# capturing activity of student during onboard character selection
@receiver(post_save, sender=Student)
def create_activity_on_onboarded(sender, instance, created, update_fields=None, **kwargs):
    if update_fields and 'onboarded' in update_fields:
        Activity.objects.create(
            actor=instance.gen_user.student,
            type=ActivityTypes.ON_BOARDED,
            action_object=instance,
            target=instance.gen_user.student
        )

# TODO: Need to fix this
# # capturing activity of student/teacher during journal posting
# @receiver(post_save, sender=JournalPost)
# def create_activity_for_journal(sender, instance, created, **kwargs):
#     if created:
#         activity_type = ActivityTypes.JOURNAL_ENTRY_BY_TEACHER
#         if instance.journal_type == JournalTypes.STUDENT_POST:
#             activity_type = ActivityTypes.JOURNAL_ENTRY_BY_STUDENT
#         Activity.objects.create(
#             actor=instance.teacher,
#             type=activity_type,
#             action_object=instance,
#             target=instance.student
#         )
