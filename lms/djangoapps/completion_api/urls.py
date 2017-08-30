"""
URLs for the completion API
"""

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^course/$', views.CompletionListView.as_view()),
    url(r'^course/(?P<course_key>.*)/$', views.CompletionDetailView.as_view()),
]
