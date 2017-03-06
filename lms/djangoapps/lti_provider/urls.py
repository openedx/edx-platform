"""
LTI Provider API endpoint urls.
"""

from django.conf import settings
from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',

    url(
        r'^courses/{course_id}/{usage_id}$'.format(
            course_id=settings.COURSE_ID_PATTERN,
            usage_id=settings.USAGE_ID_PATTERN
        ),
        'lti_provider.views.lti_launch', name="lti_provider_launch"),
)
