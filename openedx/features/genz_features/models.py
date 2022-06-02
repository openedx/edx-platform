from uuid import uuid4

from django.conf import settings
from django.db import models


USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class GenzUser(models.Model):
    LEARNER = 'Student'
    TEACHER = 'Faculty'
    AFFILIATE = 'Affiliate'
    EMPLOYEE = 'Employee'

    user = models.OneToOneField(USER_MODEL, on_delete=models.CASCADE)
    user_role = models.CharField(blank=True, null=True, max_length=32, choices=(
        (LEARNER, 'Learner'),
        (TEACHER, 'Teacher'),
        (AFFILIATE, 'Affiliate'),
        (EMPLOYEE, 'Employee'),
    ))
    organisation_id = models.CharField(max_length=128, null=True, blank=True)
    organisation_name = models.CharField(max_length=64, null=True, blank=True)
    year_of_entry = models.CharField(max_length=32, null=True, blank=True)
    registration_group = models.CharField(max_length=32, null=True, blank=True)
    teacher_id = models.CharField(max_length=128,null=True, blank=True)
