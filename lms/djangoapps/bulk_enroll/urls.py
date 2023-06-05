"""
URLs for the Bulk Enrollment API
"""


from django.conf.urls import url

from .views import BulkEnrollView

urlpatterns = [
    url(r'^bulk_enroll', BulkEnrollView.as_view(), name='bulk_enroll'),
]
