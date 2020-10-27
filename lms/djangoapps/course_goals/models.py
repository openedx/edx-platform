"""
Course Goals Models
"""
from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from opaque_keys.edx.django.models import CourseKeyField
from model_utils import Choices

from .api import add_course_goal, remove_course_goal
from course_modes.models import CourseMode
from student.models import CourseEnrollment


# Each goal is represented by a goal key and a string description.
GOAL_KEY_CHOICES = Choices(
    ('certify', _('Earn a certificate')),
    ('complete', _('Complete the course')),
    ('explore', _('Explore the course')),
    ('unsure', _('Not sure yet')),
)


class CourseGoal(models.Model):
    """
    Represents a course goal set by a user on the course home page.
    """
    user = models.ForeignKey(User, blank=False, on_delete=models.CASCADE)
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


@receiver(models.signals.post_save, sender=CourseEnrollment, dispatch_uid="update_course_goal_on_enroll_change")
def update_course_goal_on_enroll_change(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Updates goals as follows on enrollment changes:
    1) Set the course goal to 'certify' when the user enrolls as a verified user.
    2) Remove the course goal when the user's enrollment is no longer active.
    """
    course_id = str(instance.course_id).decode('utf8', 'ignore')
    if not instance.is_active:
        remove_course_goal(instance.user, course_id)
    elif instance.mode == CourseMode.VERIFIED:
        add_course_goal(instance.user, course_id, GOAL_KEY_CHOICES.certify)
