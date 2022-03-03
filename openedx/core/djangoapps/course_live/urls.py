"""
course live API URLs.
"""


from django.conf import settings
from django.urls import re_path

from openedx.core.djangoapps.course_live.views import CourseLiveConfigurationView

urlpatterns = [
    re_path(fr'^course/{settings.COURSE_KEY_PATTERN}/$',
            CourseLiveConfigurationView.as_view(), name='course_live'),
]
