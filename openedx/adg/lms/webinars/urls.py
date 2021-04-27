"""
All urls for webinars app
"""
from django.urls import path

from .views import WebinarDetailView

urlpatterns = [
    path('<int:pk>/', WebinarDetailView.as_view(), name='webinar_event'),
]
