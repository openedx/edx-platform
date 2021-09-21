"""Django models for overrides app"""

from django.contrib.auth.models import User
from django.core.validators import MaxLengthValidator, MinLengthValidator, RegexValidator
from django.db import models
from django.utils.translation import ugettext as _

from openedx.features.pakx.lms.overrides.utils import validate_text_for_emoji
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
    grade = models.CharField(max_length=4, default=None, null=True)
    email_reminder_status = models.PositiveSmallIntegerField(db_index=True, choices=REMINDER_STATES,
                                                             default=NO_EMAIL_SENT)

    class Meta:
        verbose_name_plural = 'Course Progress Stats'


class ContactUs(models.Model):
    """
    Model to store the records of contact us form data
    """
    full_name = models.CharField(
        max_length=24,
        validators=[
            validate_text_for_emoji,
            MinLengthValidator(limit_value=3, message='Name should be of minimum 3 chars.'),
            RegexValidator(message=_('Name can only contain alphabets.'), regex='^[a-zA-Z ]*$')
        ]
    )
    email = models.EmailField()
    organization = models.CharField(max_length=40, null=True, blank=True, validators=[validate_text_for_emoji])
    phone = models.CharField(
        max_length=16,
        validators=[
            MinLengthValidator(limit_value=11, message=_('Phone number should be of minimum 11 chars.')),
            RegexValidator(message=_('Phone number can only contain numbers.'), regex='^\\+?1?\\d*$')
        ]
    )
    message = models.TextField(
        verbose_name=_('How can we help you?'),
        validators=[MaxLengthValidator(4000, message=_('Message should be of maximum 4000 chars.')), validate_text_for_emoji]
    )
    created_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Contact Us'
