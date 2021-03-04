"""
Contains all the URLs
"""


from django.conf import settings
from django.conf.urls import url

from openedx.core.djangoapps.courseware_api import views

urlpatterns = [
    url(fr'^course/{settings.COURSE_KEY_PATTERN}',
        views.CoursewareInformation.as_view(),
        name="courseware-api"),
    url(fr'^sequence/{settings.USAGE_KEY_PATTERN}',
        views.SequenceMetadata.as_view(),
        name="sequence-api"),
    url(fr'^resume/{settings.COURSE_KEY_PATTERN}',
        views.Resume.as_view(),
        name="resume-api"),
    url(fr'^celebration/{settings.COURSE_KEY_PATTERN}',
        views.Celebration.as_view(),
        name="celebration-api"),
]
