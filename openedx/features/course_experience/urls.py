"""
Defines URLs for the course experience.
"""

from django.conf.urls import url

from views.course_home import CourseHomeView
from views.course_outline import CourseOutlineFragmentView

urlpatterns = [
    url(
        r'^$',
        CourseHomeView.as_view(),
        name='edx.course_experience.course_home',
    ),
    url(
        r'^outline_fragment$',
        CourseOutlineFragmentView.as_view(),
        name='edx.course_experience.course_outline_fragment_view',
    ),
]
