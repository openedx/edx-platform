""" Groups API URI specification """
from django.conf.urls import patterns, url

from rest_framework.urlpatterns import format_suffix_patterns

from api_manager.groups import views as groups_views

urlpatterns = patterns(
    '',
    url(r'/*$^', groups_views.GroupsList.as_view()),
    url(r'^(?P<group_id>[0-9]+)$', groups_views.GroupsDetail.as_view()),
    url(r'^(?P<group_id>[0-9]+)/courses/*$', groups_views.GroupsCoursesList.as_view()),
    url(r'^(?P<group_id>[0-9]+)/courses/(?P<course_id>[a-zA-Z0-9/_:]+)$', groups_views.GroupsCoursesDetail.as_view()),
    url(r'^(?P<group_id>[0-9]+)/users/*$', groups_views.GroupsUsersList.as_view()),
    url(r'^(?P<group_id>[0-9]+)/users/(?P<user_id>[0-9]+)$', groups_views.GroupsUsersDetail.as_view()),
    url(r'^(?P<group_id>[0-9]+)/groups/*$', groups_views.GroupsGroupsList.as_view()),
    url(r'^(?P<group_id>[0-9]+)/groups/(?P<related_group_id>[0-9]+)$', groups_views.GroupsGroupsDetail.as_view()),
)

urlpatterns = format_suffix_patterns(urlpatterns)
