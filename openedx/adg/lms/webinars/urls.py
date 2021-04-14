"""
All urls for webinars app
"""
from django.urls import path

from .views import webinar_description_page_view

urlpatterns = [
    path('', webinar_description_page_view, name='webinar_event'),
]
