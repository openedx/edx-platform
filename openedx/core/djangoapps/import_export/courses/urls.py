"""
URLs for course publishing API
"""
from django.conf.urls import patterns, url
from django.conf import settings

from .views import FullCourseImportExport, FullCourseImportStatus


urlpatterns = patterns(
    'api.courses.views',
    url(
        r'^{}$'.format(settings.COURSELIKE_KEY_PATTERN),
        FullCourseImportExport.as_view(),
        name='course_import_export_handler',
    ),
    url(
        r'^{}/import_status/(?P<filename>.+)$'.format(
            settings.COURSELIKE_KEY_PATTERN
        ),
        FullCourseImportStatus.as_view(),
        name='course_import_status_handler',
    ),
)
