"""
Defines URLs for the course experience.
"""

from django.conf.urls import url

from views.course_home import CourseHomeView, CourseHomeFragmentView
from views.course_outline import CourseOutlineFragmentView
from views.course_updates import CourseUpdatesFragmentView, CourseUpdatesView
from views.welcome_message import WelcomeMessageFragmentView

urlpatterns = [
    url(
        r'^$',
        CourseHomeView.as_view(),
        name='openedx.course_experience.course_home',
    ),
    url(
        r'^updates$',
        CourseUpdatesView.as_view(),
        name='openedx.course_experience.course_updates',
    ),
    url(
        r'^home_fragment$',
        CourseHomeFragmentView.as_view(),
        name='openedx.course_experience.course_home_fragment_view',
    ),
    url(
        r'^outline_fragment$',
        CourseOutlineFragmentView.as_view(),
        name='openedx.course_experience.course_outline_fragment_view',
    ),
    url(
        r'^updates_fragment$',
        CourseUpdatesFragmentView.as_view(),
        name='openedx.course_experience.course_updates_fragment_view',
    ),
    url(
        r'^welcome_message_fragment$',
        WelcomeMessageFragmentView.as_view(),
        name='openedx.course_experience.welcome_message_fragment_view',
    ),
]
