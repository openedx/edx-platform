"""
"""
from django.db import models
from student.models import User


class CourseSoftware(models.Model):
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    course_id = models.CharField(max_length=255)

    def __unicode__(self):
        return u'{0} for {1}'.format(self.name, self.course_id)


class UserLicense(models.Model):
    software = models.ForeignKey(CourseSoftware, db_index=True)
    user = models.ForeignKey(User, null=True)
    serial = models.CharField(max_length=255)
