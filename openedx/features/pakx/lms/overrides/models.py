"""Django models for overrides app"""

from django.contrib.auth.models import User
from django.db import models
from opaque_keys.edx.django.models import CourseKeyField


class CourseProgressStats(models.Model):
    """
    Model to store the records of stats related to course progress and emails to learners
    """
    NO_EMAIL_SENT = 0
    REMINDER_SENT = 1
    COURSE_COMPLETED = 2
    REMINDER_STATES = (
        (NO_EMAIL_SENT, 'No email sent'),
        (REMINDER_SENT, 'Reminder email sent'),
        (COURSE_COMPLETED, 'Course completion email sent')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_id = CourseKeyField(db_index=True, max_length=255)
    completion_date = models.DateTimeField(blank=True, default=None, null=True)
    progress = models.FloatField(default=0.0)
    grade = models.CharField(max_length=4, default=None)
    email_reminder_status = models.PositiveSmallIntegerField(db_index=True, choices=REMINDER_STATES,
                                                             default=NO_EMAIL_SENT)

    class Meta:
        verbose_name_plural = 'Course Progress Stats'
        unique_together = ('user', 'course_id',)

    def __str__(self):
        return "{} email_status:{} progress:{}".format(self.user.email, self.email_reminder_status,
                                                       self.progress)
