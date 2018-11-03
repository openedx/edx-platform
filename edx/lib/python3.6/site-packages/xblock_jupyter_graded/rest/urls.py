"""
Defines a URL to return a notebook html page to be used in an iframe
"""
from django.conf.urls import url

from xblock_jupyter_graded.rest.views import (
    DownloadStudentNBView, DownloadInstructorNBView, DownloadAutogradedNBView
)
from django.contrib.auth.decorators import login_required

app_name = 'xblock_jupyter_graded'

urlpatterns = [
    url(
    r'^download/student_nb/(?P<course_id>.+)/(?P<unit_id>.+)/(?P<filename>.+)$',
        login_required(DownloadStudentNBView.as_view()),
        name='jupyter_student_dl'
    ),
    url(
    r'^download/instructor_nb/(?P<course_id>.+)/(?P<unit_id>.+)/(?P<filename>.+)$',
        login_required(DownloadInstructorNBView.as_view()),
        name='jupyter_instructor_dl'
    ),
    url(
    r'^download/autograded_nb/(?P<course_id>.+)/(?P<unit_id>.+)/(?P<filename>.+)$',
        login_required(DownloadAutogradedNBView.as_view()),
        name='jupyter_autograded_dl'
    ),
]



