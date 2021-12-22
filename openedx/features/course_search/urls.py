"""
Defines URLs for course search.
"""

from .views.course_search import CourseSearchFragmentView, CourseSearchView
from django.urls import path

urlpatterns = [
    path('', CourseSearchView.as_view(),
         name='openedx.course_search.course_search_results',
         ),
    path('home_fragment', CourseSearchFragmentView.as_view(),
         name='openedx.course_search.course_search_results_fragment_view',
         ),
]
