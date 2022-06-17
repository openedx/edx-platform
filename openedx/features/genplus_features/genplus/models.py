from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django_extensions.db.models import TimeStampedModel
from openedx.features.genplus_features.genplus_learning.models import Skill, YearGroup

USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class School(TimeStampedModel):
    guid = models.CharField(primary_key=True, max_length=128)
    name = models.CharField(max_length=64)
    external_id = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class Class(TimeStampedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    group_id = models.CharField(primary_key=True, max_length=128)
    name = models.CharField(max_length=128)
    year_group = models.ForeignKey(YearGroup, on_delete=models.SET_NULL, null=True)
    is_visible = models.BooleanField(default=False, help_text='Manage Visibility to Genplus platform')

    def __str__(self):
        return self.name


class Character(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    skills = models.ManyToManyField(Skill, related_name='skills')
    profile_pic = models.ImageField(upload_to='gen_plus_avatars',
                                    help_text='Upload the image which will be seen by student on their dashboard')
    standing = models.ImageField(upload_to='gen_plus_avatars',
                                 help_text='Provide standing image of character')
    running = models.ImageField(upload_to='gen_plus_avatars',
                                help_text='Provide running image of character')
    crouching = models.ImageField(upload_to='gen_plus_avatars',
                                  help_text='Provide crouching image of character')
    jumping = models.ImageField(upload_to='gen_plus_avatars',
                                help_text='Provide jumping image of character')

    def __str__(self):
        return self.name


class GenUser(models.Model):
    STUDENT = 'Student'
    FACULTY = 'Faculty'
    AFFILIATE = 'Affiliate'
    EMPLOYEE = 'Employee'
    TEACHING_STAFF = 'TeachingStaff'
    NON_TEACHING_STAFF = 'NonTeachingStaff'

    user = models.OneToOneField(USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(blank=True, null=True, max_length=32, choices=(
        (STUDENT, 'Student'),
        (FACULTY, 'Faculty'),
        (AFFILIATE, 'Affiliate'),
        (EMPLOYEE, 'Employee'),
        (TEACHING_STAFF, 'TeachingStaff'),
        (NON_TEACHING_STAFF, 'NonTeachingStaff'),
    ))
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True)
    year_of_entry = models.CharField(max_length=32, null=True, blank=True)
    registration_group = models.CharField(max_length=32, null=True, blank=True)

    @property
    def is_student(self):
        return self.role == self.STUDENT

    @property
    def is_teacher(self):
        return self.role == self.TEACHING_STAFF


class Teacher(models.Model):
    user_profile = models.OneToOneField(GenUser, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to='gen_plus_teachers', null=True)
    classes = models.ManyToManyField(Class, related_name='classes')


class Student(models.Model):
    user_profile = models.OneToOneField(GenUser, on_delete=models.CASCADE)
    character = models.ForeignKey(Character,on_delete=models.SET_NULL, null=True)
    on_board = models.BooleanField(default=False)
    year_groups = models.ManyToManyField(YearGroup, related_name='year_groups')


class TempStudent(TimeStampedModel):
    username = models.CharField(max_length=128, unique=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


@receiver(post_save, sender=GenUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == GenUser.STUDENT:
            Student.objects.create(user_profile=instance)
        elif instance.role == GenUser.TEACHING_STAFF:
            Teacher.objects.create(user_profile=instance)
