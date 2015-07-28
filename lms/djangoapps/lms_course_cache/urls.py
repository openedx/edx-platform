"""
URLs for course_info API
"""
from django.conf.urls import patterns, url
from django.conf import settings

from .views import structure_view

urlpatterns = patterns(
    'lms_course_cache.views',
    url(
        r'^{}/structure$'.format(settings.COURSE_ID_PATTERN),
        structure_view,
        name='structure_view'
    )
)
