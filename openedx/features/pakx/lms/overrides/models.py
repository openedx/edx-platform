from django.db import models
from django.contrib.auth.models import User

from opaque_keys.edx.django.models import CourseKeyField
# Create your models here.


class CourseProgressEmailModel(models.Model):
    """
    Model to store the records of sent emails to learners
    """

    REMINDER_STATES = (
        (0, 'No email sent'),
        (1, 'Reminder email sent'),
        (2, 'Course completion email sent')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_id = CourseKeyField(db_index=True, max_length=255)
    status = models.PositiveSmallIntegerField(db_index=True, choices=REMINDER_STATES,
                                              default=0)

    class Meta:
        unique_together = ('user', 'course_id',)

    def __str__(self):
        return "{} status:{}".format(self.user.email, self.status)
