"""
URLs for the Agreements API
"""

from django.conf import settings
from django.conf.urls import url

from .views import IntegritySignatureView

urlpatterns = [
    url(r'^integrity_signature/{course_id}$'.format(
        course_id=settings.COURSE_ID_PATTERN
    ), IntegritySignatureView.as_view(), name='integrity_signature'),
]
