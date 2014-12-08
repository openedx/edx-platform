""" Groups API URI specification """
from django.conf import settings
from django.conf.urls import patterns, url

from rest_framework.urlpatterns import format_suffix_patterns

from server_api.groups import views as groups_views

COURSE_ID_PATTERN = settings.COURSE_ID_PATTERN

urlpatterns = patterns(
    '',
    url(r'^(?P<group_id>[0-9]+)/courses/{}$'.format(COURSE_ID_PATTERN), groups_views.GroupsCoursesDetail.as_view(), name='groups-courses-detail'),
    url(r'^(?P<group_id>[0-9]+)/courses/*$', groups_views.GroupsCoursesList.as_view(), name='groups-courses-list'),
    url(r'^(?P<group_id>[0-9]+)/users/(?P<user_id>[0-9]+)$', groups_views.GroupsUsersDetail.as_view(), name='groups-users-detail'),
    url(r'^(?P<group_id>[0-9]+)/users/*$', groups_views.GroupsUsersList.as_view(), name='groups-users-list'),
    url(r'^(?P<group_id>[0-9]+)/groups/(?P<related_group_id>[0-9]+)$', groups_views.GroupsGroupsDetail.as_view(), name='groups-groups-list'),
    url(r'^(?P<group_id>[0-9]+)/groups/*$', groups_views.GroupsGroupsList.as_view(), name='groups-groups-list'),
    url(r'^(?P<group_id>[0-9]+)$', groups_views.GroupsDetail.as_view(), name='group-detail'),
    url(r'/*$^', groups_views.GroupsList.as_view(), name='groups-list'),
)

urlpatterns = format_suffix_patterns(urlpatterns)
