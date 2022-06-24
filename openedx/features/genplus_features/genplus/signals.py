from django.dispatch import receiver
from django.conf import settings
from django.db.models.signals import post_save, m2m_changed
from .models import GenUser, Student, Teacher, TempUser
from openedx.features.genplus_features.genplus_learning.access import change_access
from openedx.features.genplus_features.genplus_learning.roles import ProgramInstructorRole

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


@receiver(m2m_changed, sender=Teacher.classes.through)
def teacher_classes_changed(sender, instance, action, **kwargs):
    pk_set = kwargs.pop('pk_set', None)
    if action == "post_add":
        access_action = 'allow'
    elif action == "pre_remove":
        access_action = 'revoke'
    else:
        return

    if isinstance(instance, Teacher) and action in ["post_add", "pre_remove"]:
        classes = instance.classes.filter(group_id__in=pk_set)
        programs = set()
        for gen_class in classes:
            current_program = gen_class.current_program
            if current_program:
                programs.add(current_program)

        for program in programs:
            change_access(program, instance.gen_user, ProgramInstructorRole.ROLE_NAME, access_action)
