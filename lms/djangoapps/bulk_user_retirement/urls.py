"""
Defines the URL route for this app.
"""

from .views import BulkUsersRetirementView
from django.urls import path


urlpatterns = [
    path('v1/accounts/bulk_retire_users', BulkUsersRetirementView.as_view(),
        name='bulk_retirement_api'
    ),
]
