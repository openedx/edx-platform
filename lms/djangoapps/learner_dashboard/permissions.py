"""
Permissions for program discussion api
"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions, status
from rest_framework.exceptions import APIException

from lms.djangoapps.program_enrollments.api import get_program_enrollment


class IsEnrolledInProgram(permissions.BasePermission):
    """Permission that checks to see if the user is enrolled in the course or is staff."""
    def has_permission(self, request, view):

        """Returns true if the user is enrolled in program"""
        if not view.program:
            raise ProgramNotFound

        try:
            get_program_enrollment(program_uuid=view.kwargs.get('program_uuid'), user=request.user)
        except ObjectDoesNotExist:
            return False
        return True


class ProgramNotFound(APIException):
    """
    custom exception class for Program not found  error
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Program not found for provided uuid'
    default_code = 'program_not_found'
