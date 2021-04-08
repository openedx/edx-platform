"""
Defines the URL route for this app.
"""

from django.conf.urls import url

from .views import BulkUsersRetirementView


urlpatterns = [
    url(
        r'v1/accounts/bulk_retire_users$',
        BulkUsersRetirementView.as_view(),
        name='bulk_retirement_api'
    ),
]
