"""Django models for overrides app"""

from django.db import models

from student.models import CourseEnrollment


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
    enrollment = models.OneToOneField(CourseEnrollment, on_delete=models.CASCADE,
                                      related_name='enrollment_stats', null=True, blank=True)
    completion_date = models.DateTimeField(blank=True, default=None, null=True)
    progress = models.FloatField(default=0.0)
    grade = models.CharField(max_length=4, default=None)
    email_reminder_status = models.PositiveSmallIntegerField(db_index=True, choices=REMINDER_STATES,
                                                             default=NO_EMAIL_SENT)

    class Meta:
        verbose_name_plural = 'Course Progress Stats'
