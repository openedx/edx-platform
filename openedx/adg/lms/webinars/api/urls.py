"""
All api urls for webinars app
"""
from django.urls import re_path

from openedx.adg.lms.webinars.api.views import WebinarRegistrationView

urlpatterns = [
    re_path(
        '(?P<pk>[0-9]+)/(?P<action>register|cancel)/$', WebinarRegistrationView.as_view(), name='webinar_registration'
    ),
]

app_name = 'webinars'
