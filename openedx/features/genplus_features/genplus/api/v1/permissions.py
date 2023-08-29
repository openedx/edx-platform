from rest_framework import permissions
from openedx.features.genplus_features.genplus.models import GenUser, Class
from django.shortcuts import get_object_or_404


class IsGenUser(permissions.BasePermission):
    message = 'Current user is not a Genplus User'

    def has_permission(self, request, view):
        try:
            # check gen_user exists and related school is active
            return request.user and request.user.gen_user and request.user.gen_user.school.is_active
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


class IsUserFromSameSchool(permissions.BasePermission):
    message = 'Requested class school matches the user school'

    def has_permission(self, request, view):
        class_id = view.kwargs.get('pk', None) or view.kwargs.get('class_id', None)
        if class_id:
                requested_class = get_object_or_404(Class, pk=class_id)
                return requested_class.school.pk == request.user.gen_user.school.pk
        return False


class IsStudentOrTeacher(permissions.BasePermission):
    message = 'Current user is neither a Genplus Student or Teacher'

    def has_permission(self, request, view):
        return IsStudent().has_permission(request, view) or IsTeacher().has_permission(request, view)


class FromPrivateSchool(permissions.BasePermission):
    message = 'Current user is not from a private School'

    def has_permission(self, request, view):
        return request.user.gen_user.from_private_school


class IsAdmin(permissions.BasePermission):
    message = 'Current user is not admin'

    def has_permission(self, request, view):
        return request.user.is_superuser


