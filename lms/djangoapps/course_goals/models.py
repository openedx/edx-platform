"""
Course Goals Models
"""
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField
from model_utils import Choices


# Each goal is represented by a goal key and a string description.
GOAL_KEY_CHOICES = Choices(
    ('certify', _('Earn a certificate.')),
    ('complete', _('Complete the course.')),
    ('explore', _('Explore the course.')),
    ('unsure', _('Not sure yet.')),
)


class CourseGoal(models.Model):
    """
    Represents a course goal set by the user.
    """
    user = models.ForeignKey(User, blank=False)
    course_key = CourseKeyField(max_length=255, db_index=True)
    goal_key = models.CharField(max_length=100, choices=GOAL_KEY_CHOICES, default=GOAL_KEY_CHOICES.unsure)

    def __unicode__(self):
        return 'CourseGoal: {user} set goal to {goal} for course {course}'.format(
            user=self.user.username,
            course=self.course_key,
            goal_key=self.goal_key,
        )

    class Meta:
        unique_together = ("user", "course_key")
