import logging
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from .models import GenUser, Student, Teacher, Class, JournalPost, Activity, GenLog
from .constants import JournalTypes, ActivityTypes, GenLogTypes

USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

logger = logging.getLogger(__name__)


@receiver(post_save, sender=GenUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_student:
            Student.objects.create(gen_user=instance)
        elif instance.is_teacher:
            Teacher.objects.create(gen_user=instance)
    if not created:
        # create a gen log if school is updated for gen user
        if instance.school != instance.pre_save_instance.school:
            GenLog.objects.create(
                gen_log_type=GenLogTypes.SCHOOL_UPDATED,
                description=f'school updated for {instance.email}',
                metadata={
                    'old_school': instance.pre_save_instance.school.name,
                    'new_school': instance.school.name,
                    'email': instance.email
                }
            )


@receiver(pre_save, sender=GenUser)
def add_pre_save_instance(sender, instance, **kwargs):
    try:
        instance.pre_save_instance = GenUser.objects.get(pk=instance.pk)
    except GenUser.DoesNotExist:
        instance.pre_save_instance = instance


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


# capturing activity of student/teacher during journal posting
@receiver(post_save, sender=JournalPost)
def create_activity_for_journal(sender, instance, created, **kwargs):
    if created:
        actor_obj = None
        if instance.journal_type == JournalTypes.STUDENT_POST:
            actor_obj = instance.student
            activity_type = ActivityTypes.JOURNAL_ENTRY_BY_STUDENT
        elif instance.journal_type == JournalTypes.TEACHER_FEEDBACK:
            actor_obj = instance.teacher
            activity_type = ActivityTypes.JOURNAL_ENTRY_BY_TEACHER
        Activity.objects.create(
            actor=actor_obj,
            type=activity_type,
            action_object=instance,
            target=instance.student
        )
