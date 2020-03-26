"""
Helpers for Intercom integration.
"""

from student.auth import user_has_role
from student.models import CourseAccessRole
from student.roles import CourseCreatorRole, CourseInstructorRole, CourseStaffRole


def should_show_intercom_widget(user):
    """
    Show or hide the Intercom chat widget to different users.

    The widget should be displayed only for course creators, course staff and course admins.

    :param user: User object to check for.
    :return: bool
    """
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return False

    if user_has_role(user, CourseCreatorRole()):
        return True

    return CourseAccessRole.objects.filter(user=user, role__in=[
        CourseStaffRole.ROLE,
        CourseInstructorRole.ROLE,
    ]).exists()
