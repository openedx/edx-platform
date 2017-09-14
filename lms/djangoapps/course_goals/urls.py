"""
Course Goals API URLs
"""
from django.conf.urls import patterns, url

from course_goals.views import set_course_goal

urlpatterns = patterns(
    '',
    url(
        r'^api/v0/(?P<course_id>.+)$',
        set_course_goal,
        name='set_course_goal',
    ),
)
