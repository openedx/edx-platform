"""
Defines URLs for announcements in the LMS.
"""
from django.contrib.auth.decorators import login_required

from .views import AnnouncementsJSONView
from django.urls import path

urlpatterns = [
    path('page/<int:page>', login_required(AnnouncementsJSONView.as_view()),
         name='page',
         ),
]
