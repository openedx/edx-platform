"""
URLs for the Bulk Enrollment API
"""


from django.urls import path

from .views import BulkEnrollView

urlpatterns = [
    path('bulk_enroll', BulkEnrollView.as_view(), name='bulk_enroll'),
]
