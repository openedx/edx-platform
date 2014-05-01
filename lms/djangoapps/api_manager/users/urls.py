""" Users API URI specification """
from django.conf.urls import patterns, url

from rest_framework.urlpatterns import format_suffix_patterns

from api_manager.users import views as users_views

urlpatterns = patterns('',
    url(r'/*$^', users_views.UsersList.as_view()),
    url(r'^(?P<user_id>[0-9]+)$', users_views.UsersDetail.as_view()),
    url(r'^(?P<user_id>[0-9]+)/courses/*$', users_views.UsersCoursesList.as_view()),
    url(r'^(?P<user_id>[0-9]+)/courses/(?P<course_id>[a-zA-Z0-9/_:]+)$', users_views.UsersCoursesDetail.as_view()),
    url(r'^(?P<user_id>[0-9]+)/groups/*$', users_views.UsersGroupsList.as_view()),
    url(r'^(?P<user_id>[0-9]+)/groups/(?P<group_id>[0-9]+)$', users_views.UsersGroupsDetail.as_view()),
)

urlpatterns = format_suffix_patterns(urlpatterns)
