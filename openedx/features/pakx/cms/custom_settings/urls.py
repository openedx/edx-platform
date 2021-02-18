"""
Urls for custom settings app
"""
from django.conf import settings
from django.conf.urls import url

from .views import CourseCustomSettingsView

urlpatterns = [
    url(
        r'^settings/custom/{}$'.format(settings.COURSE_KEY_PATTERN),
        CourseCustomSettingsView.as_view(),
        name='custom_settings'
    ),
]
