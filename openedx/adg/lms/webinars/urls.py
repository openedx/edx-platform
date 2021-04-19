"""
All urls for webinars app
"""
from django.urls import re_path

from .views import WebinarRegistrationView, webinar_description_page_view

urlpatterns = [
    # TODO In LP-2623, update webinar_event re_path to path while working on webinar description page integration
    re_path('(?P<pk>[0-9]+)/$', webinar_description_page_view, name='webinar_event'),
    re_path(
        '(?P<pk>[0-9]+)/(?P<action>register|cancel)/$', WebinarRegistrationView.as_view(), name='webinar_registration'
    ),
]
