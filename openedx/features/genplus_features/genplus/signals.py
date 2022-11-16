from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from .models import GenUser, Student, Teacher, TempUser, Class, JournalPost, Activity
from .constants import JournalTypes, ActivityTypes
import logging
USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

logger = logging.getLogger(__name__)


@receiver(post_save, sender=GenUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            user_pk = instance.user.pk
            # check if temp_user with same username,email exists
            gen_user = GenUser.objects.get(temp_user__email=instance.user.email)
            gen_user.user = get_user_model().objects.get(pk=user_pk)
            # delete current genUser
            GenUser.objects.filter(pk=instance.pk).delete()
            gen_user.save()
            # delete TempUser at the end
            TempUser.objects.get(pk=gen_user.temp_user.id).delete()
        except Exception as e:
            logger.exception(str(e))
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
