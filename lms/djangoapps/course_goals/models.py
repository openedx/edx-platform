"""
Course Goals Models
"""
from django.contrib.auth.models import User
from django.db import models
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class CourseGoal(models.Model):
    """
    Represents a course goal set by a user on the course home page.

    The goal_key represents the goal key that maps to a translated
    string through using the CourseGoalOption class.
    """
    GOAL_KEY_CHOICES = (
        ('certify', 'Earn a certificate.'),
        ('complete', 'Complete the course.'),
        ('explore', 'Explore the course.'),
        ('unsure', 'Not sure yet.'),
    )

    user = models.ForeignKey(User, blank=False)
    course_key = CourseKeyField(max_length=255, db_index=True)
    goal_key = models.CharField(max_length=100, choices=GOAL_KEY_CHOICES, default='unsure')

    def __unicode__(self):
        return 'CourseGoal: {user} set goal to {goal} for course {course}'.format(
            user=self.user.username,
            course=self.course_key,
            goal_key=self.goal_key,
        )

    class Meta:
        unique_together = ("user", "course_key")
