"""
Common utilities for use along with the course blocks.
"""


import json

from lms.djangoapps.courseware.models import StudentModule


def get_student_module_as_dict(user, course_key, block_key):
    """
    Get the student module as a dict for the given user for the given block.

    Arguments:
        user (User)
        course_key (CourseLocator)
        block_key (BlockUsageLocator)

    Returns:
        StudentModule as a (possibly empty) dict.
    """
    if not user.is_authenticated:
        return {}

    try:
        student_module = StudentModule.objects.get(
            student=user,
            course_id=course_key,
            module_state_key=block_key,
        )
    except StudentModule.DoesNotExist:
        student_module = None

    if student_module:
        return json.loads(student_module.state)
    else:
        return {}
