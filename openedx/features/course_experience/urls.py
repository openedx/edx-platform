"""
Defines URLs for the course experience.
"""

from django.urls import path
from .views.course_dates import CourseDatesFragmentMobileView
from .views.course_home import CourseHomeFragmentView, CourseHomeView
from .views.course_outline import CourseOutlineFragmentView
from .views.course_updates import CourseUpdatesFragmentView, CourseUpdatesView
from .views.latest_update import LatestUpdateFragmentView
from .views.welcome_message import WelcomeMessageFragmentView, dismiss_welcome_message

COURSE_HOME_VIEW_NAME = 'openedx.course_experience.course_home'
COURSE_DATES_FRAGMENT_VIEW_NAME = 'openedx.course_experience.mobile_dates_fragment_view'

urlpatterns = [
    path('', CourseHomeView.as_view(),
         name=COURSE_HOME_VIEW_NAME,
         ),
    path('updates', CourseUpdatesView.as_view(),
         name='openedx.course_experience.course_updates',
         ),
    path('home_fragment', CourseHomeFragmentView.as_view(),
         name='openedx.course_experience.course_home_fragment_view',
         ),
    path('outline_fragment', CourseOutlineFragmentView.as_view(),
         name='openedx.course_experience.course_outline_fragment_view',
         ),
    path('updates_fragment', CourseUpdatesFragmentView.as_view(),
         name='openedx.course_experience.course_updates_fragment_view',
         ),
    path('welcome_message_fragment', WelcomeMessageFragmentView.as_view(),
         name='openedx.course_experience.welcome_message_fragment_view',
         ),
    path('latest_update_fragment', LatestUpdateFragmentView.as_view(),
         name='openedx.course_experience.latest_update_fragment_view',
         ),
    path('dismiss_welcome_message', dismiss_welcome_message,
         name='openedx.course_experience.dismiss_welcome_message',
         ),
    path('mobile_dates_fragment', CourseDatesFragmentMobileView.as_view(),
         name=COURSE_DATES_FRAGMENT_VIEW_NAME,
         ),
]
