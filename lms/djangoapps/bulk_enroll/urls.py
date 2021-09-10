"""
URLs for the Bulk Enrollment API
"""

from .views import BulkEnrollView
from django.urls import path

urlpatterns = [
    path('bulk_enroll', BulkEnrollView.as_view(), name='bulk_enroll'),
]
