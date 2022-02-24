"""
Defines URLs for course search.
"""

from django.urls import path
from .views.course_search import CourseSearchFragmentView, CourseSearchView

urlpatterns = [
    path('', CourseSearchView.as_view(),
         name='openedx.course_search.course_search_results',
         ),
    path('home_fragment', CourseSearchFragmentView.as_view(),
         name='openedx.course_search.course_search_results_fragment_view',
         ),
]
