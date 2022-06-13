"""
Instructor Task Django app REST API permission classes.
"""
from rest_framework import permissions

from common.djangoapps.student.api import is_user_staff_or_instructor_in_course


class CanViewOrModifyScheduledBulkCourseEmailTasks(permissions.BasePermission):
    """
    Permission class that ensures a user is allowed to interact with the bulk course messages in a given course-run.
    """
    def has_permission(self, request, view):
        """
        Only course-staff/instructors or staff users should be able to modify the bulk course email messages or
        schedules.
        """
        user = request.user
        if user and user.is_authenticated:
            course_id = view.kwargs['course_id']
            return is_user_staff_or_instructor_in_course(user, course_id)

        return False
