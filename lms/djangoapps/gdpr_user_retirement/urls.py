"""
Defines the URL route for this app.
"""

from django.conf.urls import url

from .views import GDPRUsersRetirementView


urlpatterns = [
    url(
        r'v1/accounts/gdpr_retire_users$',
        GDPRUsersRetirementView.as_view(),
        name='gdpr_retirement_api'
    ),
]
