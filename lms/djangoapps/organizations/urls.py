""" Organizations API URI specification """
from django.conf.urls import patterns, url

from organizations import views as organizations_views


urlpatterns = patterns(
    '',
    url(r'^(?P<organization_id>[0-9]+)/groups/(?P<group_id>[0-9]+)/users$',
        organizations_views.OrganizationsGroupsUsersList.as_view()),
)
