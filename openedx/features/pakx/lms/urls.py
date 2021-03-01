"""
Urls for pakx lms apps
"""
from django.conf import settings
from django.conf.urls import include, url

from openedx.features.pakx.lms.overrides.views import course_about, courses

pakx_url_patterns = [
    # URL for overrides app
    url(r'', include('openedx.features.pakx.lms.overrides.urls')),

    url(r'^dashboard/?$', courses, name='dashboard'),

    url(r'^courses/?/{section}$'.format(
            section=r'(?P<section>[a-z-]+)'
        ),
        courses,
        name='courses',
    ),
    url(r'^courses/?$', courses, name='courses'),

    url(
        r'^courses/{category}/{course_id}/about$'.format(
            category=r'(?P<category>[a-z-]+)',
            course_id=settings.COURSE_ID_PATTERN,
        ),
        course_about,
        name='about_course_with_category',
    ),
]
