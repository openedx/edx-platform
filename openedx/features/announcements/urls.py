"""
Defines URLs for announcements in the LMS.
"""


from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from .views import AnnouncementsJSONView

urlpatterns = [
    url(
        r'^page/(?P<page>\d+)$',
        login_required(AnnouncementsJSONView.as_view()),
        name='page',
    ),
]
