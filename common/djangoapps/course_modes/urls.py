from django.conf import settings
from django.conf.urls import url

from course_modes.views import ChooseModeView, create_mode

urlpatterns = [
    url(r'^choose/{}/$'.format(settings.COURSE_ID_PATTERN), ChooseModeView.as_view(), name='course_modes_choose'),
]

# Enable verified mode creation
if settings.FEATURES.get('MODE_CREATION_FOR_TESTING'):
    urlpatterns += [
        url(r'^create_mode/{}/$'.format(settings.COURSE_ID_PATTERN), create_mode, name='create_mode'),
    ]
