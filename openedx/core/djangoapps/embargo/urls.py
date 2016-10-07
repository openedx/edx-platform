"""URLs served by the embargo app. """

from django.conf.urls import patterns, url

from .views import CourseAccessMessageView


urlpatterns = patterns(
    'openedx.core.djangoapps.embargo.views',
    url(
        r'^blocked-message/(?P<access_point>enrollment|courseware)/(?P<message_key>.+)/$',
        CourseAccessMessageView.as_view(),
        name='embargo_blocked_message',
    ),
)
