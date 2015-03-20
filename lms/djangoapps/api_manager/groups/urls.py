""" Groups API URI specification """
from django.conf import settings
from django.conf.urls import patterns, url

from rest_framework.urlpatterns import format_suffix_patterns

from api_manager.groups import views as groups_views

COURSE_ID_PATTERN = settings.COURSE_ID_PATTERN
GROUP_ID_PATTERN = r'(?P<group_id>[0-9]+)'

urlpatterns = patterns(
    '',
    url(r'/*$^', groups_views.GroupsList.as_view()),
    url(r'^{0}/courses/{1}$'.format(GROUP_ID_PATTERN, COURSE_ID_PATTERN), groups_views.GroupsCoursesDetail.as_view()),
    url(r'^{0}/courses/*$'.format(GROUP_ID_PATTERN), groups_views.GroupsCoursesList.as_view()),
    url(r'^{0}/organizations/*$'.format(GROUP_ID_PATTERN), groups_views.GroupsOrganizationsList.as_view()),
    url(r'^{0}/workgroups/*$'.format(GROUP_ID_PATTERN), groups_views.GroupsWorkgroupsList.as_view()),
    url(r'^{0}/users/*$'.format(GROUP_ID_PATTERN), groups_views.GroupsUsersList.as_view()),
    url(r'^{0}/users/(?P<user_id>[0-9]+)$'.format(GROUP_ID_PATTERN), groups_views.GroupsUsersDetail.as_view()),
    url(r'^{0}/groups/*$'.format(GROUP_ID_PATTERN), groups_views.GroupsGroupsList.as_view()),
    url(r'^{0}/groups/(?P<related_group_id>[0-9]+)$'.format(GROUP_ID_PATTERN), groups_views.GroupsGroupsDetail.as_view()),
    url(r'^{0}$'.format(GROUP_ID_PATTERN), groups_views.GroupsDetail.as_view()),
)

urlpatterns = format_suffix_patterns(urlpatterns)
