from uuid import uuid4

from django.conf import settings
from django.db import models
from django_extensions.db.models import TimeStampedModel

USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class School(TimeStampedModel):
    guid = models.CharField(primary_key=True, max_length=128)
    name = models.CharField(max_length=64)
    external_id = models.CharField(max_length=32)


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
