"""
Labster API URI specification.

Patterns here should simply point to version-specific patterns.
"""
from django.conf import settings
from django.conf.urls import patterns, url, include

urlpatterns = patterns(
    '',
    url(
        r'^course/?$', 'openedx.core.djangoapps.labster.course.views.course_handler',
        name='course_handler'
    ),
    url(
        r'^course/({})/?$'.format(settings.COURSE_KEY_PATTERN),
        'openedx.core.djangoapps.labster.course.views.course_handler',
        name='course_handler_detail'
    )
)
