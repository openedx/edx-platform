"""
    Open edX endpoints overriden with our own views
"""

from django.conf.urls import url, patterns

from . import views

urlpatterns = patterns(
    url(r'^courses/?$', views.courses, name="courses"),
)
