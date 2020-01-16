"""URLs served by the embargo app. """


from django.conf.urls import url

from .views import CheckCourseAccessView, CourseAccessMessageView

app_name = 'embargo'
urlpatterns = [
    url(
        r'^blocked-message/(?P<access_point>enrollment|courseware)/(?P<message_key>.+)/$',
        CourseAccessMessageView.as_view(),
        name='blocked_message',
    ),
    url(r'^v1/course_access/$', CheckCourseAccessView.as_view(), name='v1_course_access'),
]
