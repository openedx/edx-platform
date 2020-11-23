"""
Course Goals Models
"""


from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from opaque_keys.edx.django.models import CourseKeyField

# Each goal is represented by a goal key and a string description.
GOAL_KEY_CHOICES = Choices(
    (u'certify', _('Earn a certificate')),
    (u'complete', _('Complete the course')),
    (u'explore', _('Explore the course')),
    (u'unsure', _('Not sure yet')),
)


@python_2_unicode_compatible
class CourseGoal(models.Model):
    """
    Represents a course goal set by a user on the course home page.

    .. no_pii:
    """
    class Meta(object):
        app_label = "course_goals"
        unique_together = ("user", "course_key")

    user = models.ForeignKey(User, blank=False, on_delete=models.CASCADE)
    course_key = CourseKeyField(max_length=255, db_index=True)
    goal_key = models.CharField(max_length=100, choices=GOAL_KEY_CHOICES, default=GOAL_KEY_CHOICES.unsure)

    def __str__(self):
        return 'CourseGoal: {user} set goal to {goal} for course {course}'.format(
            user=self.user.username,
            goal=self.goal_key,
            course=self.course_key,
        )
