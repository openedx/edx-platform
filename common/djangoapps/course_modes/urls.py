from django.conf.urls import patterns, url
from django.conf import settings

from course_modes import views

urlpatterns = patterns(
    '',
    # pylint seems to dislike as_view() calls because it's a `classonlymethod` instead of `classmethod`, so we disable the warning
    url(r'^choose/{}/$'.format(settings.COURSE_ID_PATTERN), views.ChooseModeView.as_view(), name='course_modes_choose'),
)

# Enable verified mode creation
if settings.FEATURES.get('MODE_CREATION_FOR_TESTING'):
    urlpatterns += (
        url(r'^create_mode/{}/$'.format(settings.COURSE_ID_PATTERN), 'course_modes.views.create_mode', name='create_mode'),
    )
