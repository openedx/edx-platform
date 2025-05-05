"""
Python APIs exposed for the progress tracking functionality of the course home API.
"""

from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.courseware.courses import get_course_blocks_completion_summary

User = get_user_model()


def calculate_progress_for_learner_in_course(course_key: CourseKey, user: User) -> dict:
    """
    Calculate a given learner's progress in the specified course run.
    """
    summary = get_course_blocks_completion_summary(course_key, user)
    if not summary:
        return {}

    complete_count = summary.get("complete_count", 0)
    locked_count = summary.get("locked_count", 0)
    incomplete_count = summary.get("incomplete_count", 0)

    # This completion calculation mirrors the logic used in the CompletionDonutChart component on the Learning MFE's
    # Progress tab. It's duplicated here to enable backend reporting on learner progress. Ideally, this logic should be
    # refactored in the future so that the calculation is handled solely on the backend, eliminating the need for it to
    # be done in the frontend.
    num_total_units = complete_count + incomplete_count + locked_count
    if num_total_units == 0:
        complete_percentage = locked_percentage = incomplete_percentage = 0.0
    else:
        complete_percentage = round(complete_count / num_total_units, 2)
        locked_percentage = round(locked_count / num_total_units, 2)
        incomplete_percentage = 1.00 - complete_percentage - locked_percentage

    return {
        "complete_count": complete_count,
        "locked_count": locked_count,
        "incomplete_count": incomplete_count,
        "total_count": num_total_units,
        "complete_percentage": complete_percentage,
        "locked_percentage": locked_percentage,
        "incomplete_percentage": incomplete_percentage
    }
