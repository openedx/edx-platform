"""
Course Goals Signals
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from eventtracking import tracker

from .models import CourseGoal


@receiver(post_save, sender=CourseGoal, dispatch_uid="emit_course_goal_event")
def emit_course_goal_event(sender, instance, **kwargs):
    name = 'edx.course.goal.added' if kwargs.get('created', False) else 'edx.course.goal.updated'
    tracker.emit(
        name,
        {
            'goal_key': instance.goal_key,
        }
    )
