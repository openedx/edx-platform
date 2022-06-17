from rest_framework import permissions


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.genuser.is_student


class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.genuser.is_teacher
