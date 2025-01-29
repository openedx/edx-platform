"""
Defines URLs for announcements in the LMS.
"""
from django.contrib.auth.decorators import login_required
from django.urls import path

from .views import AnnouncementsJSONView

urlpatterns = [
    path('page/<int:page>', login_required(AnnouncementsJSONView.as_view()),
         name='page',
         ),
]
