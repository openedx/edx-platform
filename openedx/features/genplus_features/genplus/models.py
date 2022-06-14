from django.conf import settings
from django.db import models
from django_extensions.db.models import TimeStampedModel

USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class School(TimeStampedModel):
    guid = models.CharField(primary_key=True, max_length=128)
    name = models.CharField(max_length=64)
    external_id = models.CharField(max_length=32)


class Class(TimeStampedModel):
    group_id = models.CharField(primary_key=True, max_length=128)
    name = models.CharField(max_length=128)
    is_visible = models.BooleanField(default=False, help_text='Manage Visibility to Genplus platform')


class Character(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    profile_pic = models.ImageFiled(upload_to='gen_plus_avatars',
                                    help_text='Upload the image which will be seen by student on their dashboard')
    crouching = models.ImageFiled(upload_to='gen_plus_avatars',
                                  help_text='Provide crouching image of character')
    standing = models.ImageFiled(upload_to='gen_plus_avatars',
                                 help_text='Provide standing image of character')
    jumping  = models.ImageFiled(upload_to='gen_plus_avatars',
                                 help_text='Provide jumping image of character')




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


class TempStudent(TimeStampedModel):
    username = models.CharField(max_length=128, unique=True)
    email = models.EmailField(unique=True)

