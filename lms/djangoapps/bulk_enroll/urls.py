"""
URLs for the Bulk Enrollment API
"""
from django.conf.urls import patterns, url

from bulk_enroll.views import BulkEnrollView

urlpatterns = patterns(
    'bulk_enroll.views',
    url(r'^bulk_enroll', BulkEnrollView.as_view(), name='bulk_enroll'),
)
