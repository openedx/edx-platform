"""
URLs for exposing the RESTful HTTP endpoints for the Course About API.

"""
from django.conf import settings
from django.conf.urls import patterns, url
from course_about.views import CourseAboutView

urlpatterns = patterns(
    'course_about.views',
    url(
        r'^{course_key}'.format(course_key=settings.COURSE_ID_PATTERN),
        CourseAboutView.as_view(), name="courseabout"
    ),
)
