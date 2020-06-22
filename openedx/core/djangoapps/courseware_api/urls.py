"""
Contains all the URLs
"""


from django.conf import settings
from django.conf.urls import url

from openedx.core.djangoapps.courseware_api import views

urlpatterns = [
    url(r'^course/{}'.format(settings.COURSE_KEY_PATTERN),
        views.CoursewareInformation.as_view(),
        name="courseware-api"),
    url(r'^sequence/{}'.format(settings.USAGE_KEY_PATTERN),
        views.SequenceMetadata.as_view(),
        name="sequence-api"),
    url(r'^resume/{}'.format(settings.COURSE_KEY_PATTERN),
        views.Resume.as_view(),
        name="resume-api"),
    url(r'^celebration/{}'.format(settings.COURSE_KEY_PATTERN),
        views.Celebration.as_view(),
        name="celebration-api"),
]
