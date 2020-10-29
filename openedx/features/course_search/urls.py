"""
Defines URLs for course search.
"""

from __future__ import absolute_import

from django.conf.urls import url

from .views.course_search import CourseSearchFragmentView, CourseSearchView

urlpatterns = [
    url(
        r'^$',
        CourseSearchView.as_view(),
        name='openedx.course_search.course_search_results',
    ),
    url(
        r'^home_fragment$',
        CourseSearchFragmentView.as_view(),
        name='openedx.course_search.course_search_results_fragment_view',
    ),
]
