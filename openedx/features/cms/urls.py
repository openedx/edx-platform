from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^course_multiple_rerun/$", views.course_multiple_rerun_handler, name="course_multiple_rerun"),
]
