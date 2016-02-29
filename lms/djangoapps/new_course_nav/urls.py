from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from .views import NewCourseNavView


urlpatterns = patterns(
    'new_course_nav.views',
    url(r'^/$', login_required(NewCourseNavView.as_view()), name='new_course_nav')
)
