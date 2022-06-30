from rest_framework import permissions
from openedx.features.genplus_features.genplus.models import GenUser


class IsGenUser(permissions.BasePermission):
    message = 'Current user is not a Genplus User'

    def has_permission(self, request, view):
        try:
            return request.user and request.user.gen_user
        except GenUser.DoesNotExist:
            return False


class IsStudent(permissions.BasePermission):
    message = 'Current user is not a Genplus Student'

    def has_permission(self, request, view):
        return IsGenUser().has_permission(request, view) and request.user.gen_user.is_student


class IsTeacher(permissions.BasePermission):
    message = 'Current user is not a Genplus Teacher'

    def has_permission(self, request, view):
        return IsGenUser().has_permission(request, view) and request.user.gen_user.is_teacher


class IsStudentOrTeacher(permissions.BasePermission):
    message = 'Current user is neither a Genplus Student or Teacher'

    def has_permission(self, request, view):
        return IsStudent().has_permission(request, view) or IsTeacher().has_permission(request, view)
