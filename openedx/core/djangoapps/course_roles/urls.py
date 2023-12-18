"""
URL configuration for course roles api.
"""
from django.urls import path

from .views import UserPermissionsView, UserPermissionsFlagView

app_name = 'course_roles_api'

urlpatterns = [
    path('v1/user_permissions/', UserPermissionsView.as_view(), name='user_permissions'),
    path('v1/user_permissions/enabled/', UserPermissionsFlagView.as_view(), name='permission_check_flag')
]
