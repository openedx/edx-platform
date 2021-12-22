"""
Defines URLs for course bookmarks.
"""

from .views.course_bookmarks import CourseBookmarksFragmentView, CourseBookmarksView
from django.urls import path

urlpatterns = [
    path('', CourseBookmarksView.as_view(),
         name='openedx.course_bookmarks.home',
         ),
    path('bookmarks_fragment', CourseBookmarksFragmentView.as_view(),
         name='openedx.course_bookmarks.course_bookmarks_fragment_view',
         ),
]
