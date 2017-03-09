"""
Defines URLs for the course experience.
"""

from django.conf.urls import url

from views.course_bookmarks import CourseBookmarksView, CourseBookmarksFragmentView

urlpatterns = [
    url(
        r'^$',
        CourseBookmarksView.as_view(),
        name='openedx.course_bookmarks.home',
    ),
    url(
        r'^bookmarks_fragment$',
        CourseBookmarksFragmentView.as_view(),
        name='openedx.course_bookmarks.course_bookmarks_fragment_view',
    ),
]
