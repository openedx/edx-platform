"""
URLs for the Agreements API
"""

from django.conf import settings

from .views import IntegritySignatureView
from django.urls import re_path

urlpatterns = [
    re_path(r'^integrity_signature/{course_id}$'.format(
        course_id=settings.COURSE_ID_PATTERN
    ), IntegritySignatureView.as_view(), name='integrity_signature'),
]
