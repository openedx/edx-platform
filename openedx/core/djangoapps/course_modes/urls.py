"""URLs for course_mode API"""
from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.conf.urls import url

from openedx.core.djangoapps.course_modes import views

urlpatterns = [
    url(r'^choose/{}/$'.format(settings.COURSE_ID_PATTERN), views.ChooseModeView.as_view(), name='course_modes_choose'),
]

# Enable verified mode creation
if settings.FEATURES.get('MODE_CREATION_FOR_TESTING'):
    urlpatterns.append(
        url(r'^create_mode/{}/$'.format(settings.COURSE_ID_PATTERN),
            views.create_mode,
            name='create_mode'),
    )
