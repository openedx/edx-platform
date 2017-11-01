"""
LTI Provider API endpoint urls.
"""

from django.conf import settings
from django.conf.urls import url

from lti_provider.views import lti_launch

urlpatterns = [
    url(r'^courses/{course_id}/{usage_id}$'.format(
        course_id=settings.COURSE_ID_PATTERN, usage_id=settings.USAGE_ID_PATTERN),
        lti_launch,
        name="lti_provider_launch"),
]
