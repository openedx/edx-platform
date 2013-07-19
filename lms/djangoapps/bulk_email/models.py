from django.db import models
from django.contrib.auth.models import User


class Email(models.Model):
    sender = models.ForeignKey(User, default=1, blank=True, null=True)
    hash = models.CharField(max_length=128, db_index=True)
    subject = models.CharField(max_length=128, blank=True)
    html_message = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CourseEmail(Email, models.Model):
    TO_OPTIONS = (('myself', 'Myself'),
                  ('staff', 'Staff and instructors'),
                  ('all', 'All')
                  )
    course_id = models.CharField(max_length=255, db_index=True)
    to = models.CharField(max_length=64, choices=TO_OPTIONS, default='myself')

    def __unicode__(self):
        return self.subject


class Optout(models.Model):
    email = models.CharField(max_length=255, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)

    class Meta:
        unique_together = ('email', 'course_id')
