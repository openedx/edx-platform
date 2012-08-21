"""
"""

from django.db import models

from student.models import User


class Software(models.Model):
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    course_id = models.CharField(max_length=255)


class StudentLicense(models.Model):
    software = models.ForeignKey(Software, db_index=True)
    serial = models.CharField(max_length=255)
    user = models.ForeignKey(User, null=True, blank=True)
