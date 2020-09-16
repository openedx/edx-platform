"""
All utility function related to courses
"""


def get_course_structure():
    """
    Get structure of the course

    Returns:
        dict: course structure
    """
    return {
        'course': 'chapter',
        'chapter': 'sequential',
        'sequential': 'vertical',
        'vertical': 'html',
    }
