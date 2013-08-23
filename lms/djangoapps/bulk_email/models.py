"""
Models for bulk email

WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py lms schemamigration bulk_email --auto description_of_your_change
3. Add the migration file created in edx-platform/lms/djangoapps/bulk_email/migrations/


ASSUMPTIONS: modules have unique IDs, even across different module_types

"""
from django.db import models
from django.contrib.auth.models import User


class Email(models.Model):
    """
    Abstract base class for common information for an email.
    """
    sender = models.ForeignKey(User, default=1, blank=True, null=True)
    slug = models.CharField(max_length=128, db_index=True)
    subject = models.CharField(max_length=128, blank=True)
    html_message = models.TextField(null=True, blank=True)
    text_message = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CourseEmail(Email, models.Model):
    """
    Stores information for an email to a course.
    """
    # Three options for sending that we provide from the instructor dashboard:
    # * Myself: This sends an email to the staff member that is composing the email.
    #
    # * Staff and instructors: This sends an email to anyone in the staff group and
    #   anyone in the instructor group
    #
    # * All: This sends an email to anyone enrolled in the course, with any role
    #   (student, staff, or instructor)
    #
    TO_OPTIONS = (
        ('myself', 'Myself'),
        ('staff', 'Staff and instructors'),
        ('all', 'All')
    )
    course_id = models.CharField(max_length=255, db_index=True)
    to_option = models.CharField(max_length=64, choices=TO_OPTIONS, default='myself')

    def __unicode__(self):
        return self.subject


class Optout(models.Model):
    """
    Stores users that have opted out of receiving emails from a course.
    """
    user = models.ForeignKey(User, db_index=True, null=True)
    course_id = models.CharField(max_length=255, db_index=True)

    class Meta:
        unique_together = ('user', 'course_id')
