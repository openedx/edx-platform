"""
Signal handlers for AI Learning integration.

These handlers capture key events in the LMS and send them to the AI Engine
for analysis and adaptation.
"""

import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.grades.signals.signals import PROBLEM_WEIGHTED_SCORE_CHANGED

from . import api as ai_api
from .models import AdaptiveInteraction

User = get_user_model()
log = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    """
    Create AI learning profile when a new user is created.
    """
    if created and not instance.is_staff and not instance.is_superuser:
        try:
            ai_api.get_student_learning_profile(instance)
            log.info(f"Created AI learning profile for new user: {instance.id}")
        except Exception as e:
            log.error(f"Failed to create AI profile for user {instance.id}: {e}")


@receiver(post_save, sender=CourseEnrollment)
def handle_course_enrollment(sender, instance, created, **kwargs):
    """
    Notify AI Engine when a student enrolls in a course.
    """
    if created and instance.is_active:
        try:
            from .client import AIEngineClient
            client = AIEngineClient()

            client.record_interaction(
                user_id=instance.user.id,
                course_key=str(instance.course_id),
                usage_key='enrollment',
                interaction_type='enrollment',
                data={
                    'mode': instance.mode,
                    'course_id': str(instance.course_id)
                }
            )

            log.info(
                f"Recorded enrollment for user {instance.user.id} "
                f"in course {instance.course_id}"
            )
        except Exception as e:
            log.error(f"Failed to record enrollment: {e}")


@receiver(PROBLEM_WEIGHTED_SCORE_CHANGED)
def handle_problem_score_changed(sender, **kwargs):
    """
    Send problem scoring data to AI Engine for adaptation.
    """
    try:
        user_id = kwargs.get('user_id')
        course_id = kwargs.get('course_id')
        usage_id = kwargs.get('usage_id')
        weighted_earned = kwargs.get('weighted_earned')
        weighted_possible = kwargs.get('weighted_possible')

        if not all([user_id, course_id, usage_id]):
            return

        user = User.objects.get(id=user_id)

        # Calculate score percentage
        score_pct = 0
        if weighted_possible > 0:
            score_pct = (weighted_earned / weighted_possible) * 100

        # Record interaction with AI Engine
        ai_api.record_adaptive_interaction(
            user=user,
            course_key=course_id,
            usage_key=usage_id,
            interaction_type='assessment',
            interaction_data={
                'weighted_earned': weighted_earned,
                'weighted_possible': weighted_possible,
                'score_percentage': score_pct,
                'event': 'score_changed'
            }
        )

        log.info(
            f"Recorded problem score for user {user_id} in {course_id}: "
            f"{score_pct:.1f}%"
        )

    except User.DoesNotExist:
        log.warning(f"User {user_id} not found for problem score signal")
    except Exception as e:
        log.error(f"Error handling problem score change: {e}", exc_info=True)


@receiver(post_save, sender=AdaptiveInteraction)
def process_adaptive_interaction(sender, instance, created, **kwargs):
    """
    Process adaptive interactions to trigger course modifications if needed.
    """
    if not created:
        return

    try:
        # Check if AI Engine recommended any adaptations
        ai_response = instance.ai_response
        if not ai_response:
            return

        adaptations = ai_response.get('adaptations', [])

        for adaptation in adaptations:
            adaptation_type = adaptation.get('type')

            if adaptation_type == 'unlock_content':
                # Unlock next content block
                log.info(
                    f"Adaptation: Unlock content for user {instance.user.id} "
                    f"in {instance.course_key}"
                )
                # Implementation would use course structure API

            elif adaptation_type == 'add_remedial':
                # Add remedial content
                log.info(
                    f"Adaptation: Add remedial content for user {instance.user.id} "
                    f"in {instance.course_key}"
                )
                # Implementation would create/link additional content

            elif adaptation_type == 'skip_ahead':
                # Skip redundant content
                log.info(
                    f"Adaptation: Skip ahead for user {instance.user.id} "
                    f"in {instance.course_key}"
                )
                # Implementation would update progress

            elif adaptation_type == 'trigger_tutor':
                # Suggest AI tutor help
                log.info(
                    f"Adaptation: Trigger tutor for user {instance.user.id} "
                    f"in {instance.course_key}"
                )
                # Implementation would send notification or display prompt

    except Exception as e:
        log.error(f"Error processing adaptation: {e}", exc_info=True)
