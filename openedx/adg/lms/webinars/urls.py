"""
All urls for webinars app
"""
from django.urls import path, re_path

from .views import WebinarDetailView, WebinarRegistrationView

urlpatterns = [
    path('<int:pk>/', WebinarDetailView.as_view(), name='webinar_event'),
    re_path(
        '(?P<pk>[0-9]+)/(?P<action>register|cancel)/$', WebinarRegistrationView.as_view(), name='webinar_registration'
    ),
]
