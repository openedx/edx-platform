from django.dispatch import receiver
from django.conf import settings
from django.db.models.signals import post_save
from .models import GenUser, Student, Teacher, TempUser, Class

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
    if created:
        classes = Class.objects.filter(school=instance.gen_user.school)
        instance.classes.add(*classes)


@receiver(post_save, sender=Class)
def create_gen_class(sender, instance, created, **kwargs):
    if created:
        teachers = Teacher.objects.filter(gen_user__school=instance.school)
        instance.teachers.add(*teachers)
