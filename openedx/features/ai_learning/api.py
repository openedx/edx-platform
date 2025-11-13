"""
Public API for AI Learning integration.

This module provides the interface for other parts of edx-platform
to interact with the AI Learning features.
"""

import logging
from typing import Dict, List, Optional

from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey, UsageKey

from .client import AIEngineClient
from .models import AIGeneratedCourse, AdaptiveInteraction, StudentLearningProfile

User = get_user_model()
log = logging.getLogger(__name__)


def generate_course(
    user: User,
    prompt: str,
    course_org: str,
    course_number: str,
    course_run: str,
    metadata: Optional[Dict] = None
) -> AIGeneratedCourse:
    """
    Request the AI Engine to generate a new course.

    Args:
        user: User requesting the course generation
        prompt: Natural language description of desired course
        course_org: Organization identifier
        course_number: Course number
        course_run: Course run identifier
        metadata: Additional metadata for course generation

    Returns:
        AIGeneratedCourse instance tracking the generation

    Raises:
        ValueError: If prompt is empty or course identifiers are invalid
        RuntimeError: If AI Engine request fails
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    # Create the course key
    course_key = CourseKey.from_string(f"course-v1:{course_org}+{course_number}+{course_run}")

    # Create tracking record
    ai_course = AIGeneratedCourse.objects.create(
        course_key=course_key,
        creator=user,
        generation_prompt=prompt,
        generation_status='pending',
        metadata=metadata or {}
    )

    # Call AI Engine to start generation
    try:
        client = AIEngineClient()
        response = client.generate_curriculum(
            prompt=prompt,
            course_key=str(course_key),
            user_id=user.id,
            metadata=metadata
        )

        ai_course.ai_engine_course_id = response['course_id']
        ai_course.generation_status = 'generating'
        ai_course.save()

        log.info(
            f"Started AI course generation: {course_key}, "
            f"AI Engine ID: {response['course_id']}"
        )

        return ai_course

    except Exception as e:
        ai_course.generation_status = 'failed'
        ai_course.metadata['error'] = str(e)
        ai_course.save()
        log.error(f"Failed to generate course {course_key}: {e}")
        raise RuntimeError(f"Course generation failed: {e}") from e


def get_student_learning_profile(user: User) -> StudentLearningProfile:
    """
    Get or create a student's learning profile.

    Args:
        user: Student user

    Returns:
        StudentLearningProfile instance
    """
    profile, created = StudentLearningProfile.objects.get_or_create(
        user=user,
        defaults={
            'ai_engine_profile_id': f"user_{user.id}",
        }
    )

    if created:
        # Initialize profile in AI Engine
        try:
            client = AIEngineClient()
            client.create_student_profile(user_id=user.id, username=user.username)
            log.info(f"Created AI learning profile for user {user.id}")
        except Exception as e:
            log.error(f"Failed to create AI profile for user {user.id}: {e}")

    return profile


def record_adaptive_interaction(
    user: User,
    course_key: CourseKey,
    usage_key: UsageKey,
    interaction_type: str,
    interaction_data: Dict
) -> AdaptiveInteraction:
    """
    Record an adaptive interaction and send to AI Engine.

    Args:
        user: Student user
        course_key: Course identifier
        usage_key: XBlock identifier
        interaction_type: Type of interaction (assessment, tutor_chat, etc.)
        interaction_data: Data about the interaction

    Returns:
        AdaptiveInteraction instance
    """
    import time
    start_time = time.time()

    try:
        # Send to AI Engine for analysis
        client = AIEngineClient()
        ai_response = client.record_interaction(
            user_id=user.id,
            course_key=str(course_key),
            usage_key=str(usage_key),
            interaction_type=interaction_type,
            data=interaction_data
        )

        response_time_ms = int((time.time() - start_time) * 1000)

        # Save interaction record
        interaction = AdaptiveInteraction.objects.create(
            user=user,
            course_key=course_key,
            usage_key=usage_key,
            interaction_type=interaction_type,
            interaction_data=interaction_data,
            ai_response=ai_response,
            response_time_ms=response_time_ms
        )

        log.info(
            f"Recorded adaptive interaction: {interaction_type} "
            f"by user {user.id} in {course_key}"
        )

        return interaction

    except Exception as e:
        log.error(
            f"Failed to record adaptive interaction: {e}",
            exc_info=True
        )
        # Still create the record, but without AI response
        return AdaptiveInteraction.objects.create(
            user=user,
            course_key=course_key,
            usage_key=usage_key,
            interaction_type=interaction_type,
            interaction_data=interaction_data,
            ai_response={'error': str(e)}
        )


def get_adaptive_feedback(
    user: User,
    course_key: CourseKey,
    usage_key: UsageKey,
    question_data: Dict,
    answer_data: Dict
) -> Dict:
    """
    Get adaptive feedback from AI Engine for a student's answer.

    Args:
        user: Student user
        course_key: Course identifier
        usage_key: XBlock identifier
        question_data: Information about the question
        answer_data: Student's answer and metadata

    Returns:
        Dictionary containing feedback, hints, and adaptation instructions
    """
    try:
        client = AIEngineClient()
        feedback = client.get_adaptive_feedback(
            user_id=user.id,
            course_key=str(course_key),
            usage_key=str(usage_key),
            question=question_data,
            answer=answer_data
        )

        log.info(f"Generated adaptive feedback for user {user.id} in {course_key}")
        return feedback

    except Exception as e:
        log.error(f"Failed to get adaptive feedback: {e}", exc_info=True)
        return {
            'feedback': 'Unable to generate personalized feedback at this time.',
            'success': False,
            'error': str(e)
        }


def get_ai_tutor_response(
    user: User,
    course_key: CourseKey,
    usage_key: UsageKey,
    message: str,
    conversation_history: Optional[List[Dict]] = None
) -> Dict:
    """
    Get a response from the AI tutor.

    Args:
        user: Student user
        course_key: Course identifier
        usage_key: XBlock identifier where tutor is embedded
        message: Student's message to the tutor
        conversation_history: Previous messages in the conversation

    Returns:
        Dictionary containing tutor response and metadata
    """
    try:
        client = AIEngineClient()
        response = client.get_tutor_response(
            user_id=user.id,
            course_key=str(course_key),
            usage_key=str(usage_key),
            message=message,
            history=conversation_history or []
        )

        log.info(f"Generated AI tutor response for user {user.id} in {course_key}")
        return response

    except Exception as e:
        log.error(f"Failed to get AI tutor response: {e}", exc_info=True)
        return {
            'response': 'I apologize, but I\'m having trouble responding right now. Please try again in a moment.',
            'success': False,
            'error': str(e)
        }


def sync_student_profile(user: User) -> bool:
    """
    Sync student profile data from AI Engine.

    Args:
        user: Student user

    Returns:
        True if sync was successful, False otherwise
    """
    try:
        profile = get_student_learning_profile(user)

        client = AIEngineClient()
        profile_data = client.get_student_profile(user_id=user.id)

        # Update local profile with data from AI Engine
        profile.learning_style = profile_data.get('learning_style', '')
        profile.mastered_concepts = profile_data.get('mastered_concepts', [])
        profile.struggling_concepts = profile_data.get('struggling_concepts', [])
        profile.preferences = profile_data.get('preferences', {})
        profile.save()

        log.info(f"Synced learning profile for user {user.id}")
        return True

    except Exception as e:
        log.error(f"Failed to sync student profile for user {user.id}: {e}")
        return False
