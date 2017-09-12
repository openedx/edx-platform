"""
URLs for the completion API
"""

from django.conf import settings
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^course/$', views.CompletionListView.as_view()),
    url(r'^course/{}/$'.format(settings.COURSE_ID_PATTERN), views.CompletionDetailView.as_view()),
    url(r'^course/{}/blocks/{}/$'.format(
        settings.COURSE_ID_PATTERN,
        settings.USAGE_ID_PATTERN
    ), views.CompletionBlockUpdateView.as_view()),
]
