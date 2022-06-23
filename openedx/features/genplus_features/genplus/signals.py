from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed
from .models import GenUser, Student, Teacher, Class
from openedx.features.genplus_features.genplus_learning.access import allow_access, revoke_access
from openedx.features.genplus_features.genplus_learning.roles import YearGroupInstructorRole


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
    if isinstance(instance, Teacher) and action in ["post_add", "pre_remove"]:
        classes = instance.classes.filter(group_id__in=pk_set)
        year_groups = set([genclass.year_group for genclass in classes])

        if action == "post_add":
            for year_group in year_groups:
                allow_access(year_group, instance.gen_user, YearGroupInstructorRole.ROLE_NAME)
        elif action == "pre_remove":
            for year_group in year_groups:
                revoke_access(year_group, instance.gen_user, YearGroupInstructorRole.ROLE_NAME)
