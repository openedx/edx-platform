#-*- coding: utf-8 -*-

"""
Block Sturecture API URLs
"""
from django.conf.urls import patterns, url
from .views import ClearCoursesCacheView


urlpatterns = patterns(
    'block_structure.views',
    url(
        r'^clear-courses-cache/$',
        ClearCoursesCacheView.as_view(),
        name="clear-courses-cache"
    ),
)
