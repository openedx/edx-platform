"""
URL configuration for course roles api.
"""
from django.urls import path

from .views import UserPermissionsView

app_name = 'course_roles_api'

urlpatterns = [
    path('v1/user_permissions/', UserPermissionsView.as_view(), name='user_permissions'),
]
