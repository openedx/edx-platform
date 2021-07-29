"""
Course Goals Models
"""


from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from opaque_keys.edx.django.models import CourseKeyField
from simple_history.models import HistoricalRecords

# Each goal is represented by a goal key and a string description.
GOAL_KEY_CHOICES = Choices(
    ('certify', _('Earn a certificate')),
    ('complete', _('Complete the course')),
    ('explore', _('Explore the course')),
    ('unsure', _('Not sure yet')),
)

NUMBER_OF_DAYS_OPTIONS = [1, 3, 5]

User = get_user_model()


class CourseGoal(models.Model):
    """
    Represents a course goal set by a user on the course home page.

    .. no_pii:
    """
    class Meta:
        app_label = "course_goals"
        unique_together = ("user", "course_key")

    user = models.ForeignKey(User, blank=False, on_delete=models.CASCADE)
    course_key = CourseKeyField(max_length=255, db_index=True)
    # The goal a user has set for the number of days they want to learn per week
    number_of_days_with_visits_per_week_goal = models.PositiveIntegerField(default=0)
    # Controls whether a user will receive emails reminding them to stay on track with their learning goal
    subscribed_to_goal_reminders = models.BooleanField(default=False)
    goal_key = models.CharField(max_length=100, choices=GOAL_KEY_CHOICES, default=GOAL_KEY_CHOICES.unsure)
    history = HistoricalRecords()

    def __str__(self):
        return 'CourseGoal: {user} set goal to {goal} days per week for course {course}'.format(
            user=self.user.username,
            goal=self.number_of_days_with_visits_per_week_goal,
            course=self.course_key,
        )
