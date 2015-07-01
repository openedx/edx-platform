"""
Courses API URI specification
The order of the URIs really matters here, due to the slash characters present in the identifiers
"""
from django.conf import settings
from django.conf.urls import patterns, url

from rest_framework.urlpatterns import format_suffix_patterns

from api_manager.courses import views as courses_views

CONTENT_ID_PATTERN = r'(?P<content_id>[\.a-zA-Z0-9_+\/:-]+)'
COURSE_ID_PATTERN = settings.COURSE_ID_PATTERN

urlpatterns = patterns(
    '',
    url(r'^{0}/content/{1}/groups/(?P<group_id>[0-9]+)$'.format(COURSE_ID_PATTERN, CONTENT_ID_PATTERN), courses_views.CourseContentGroupsDetail.as_view()),
    url(r'^{0}/content/{1}/groups/*$'.format(COURSE_ID_PATTERN, CONTENT_ID_PATTERN), courses_views.CourseContentGroupsList.as_view()),
    url(r'^{0}/content/{1}/children/*$'.format(COURSE_ID_PATTERN, CONTENT_ID_PATTERN), courses_views.CourseContentList.as_view()),
    url(r'^{0}/content/{1}/users/*$'.format(COURSE_ID_PATTERN, CONTENT_ID_PATTERN), courses_views.CourseContentUsersList.as_view()),
    url(r'^{0}/content/{1}$'.format(COURSE_ID_PATTERN, CONTENT_ID_PATTERN), courses_views.CourseContentDetail.as_view()),
    url(r'^{0}/content/*$'.format(COURSE_ID_PATTERN), courses_views.CourseContentList.as_view()),
    url(r'^{0}/groups/(?P<group_id>[0-9]+)$'.format(COURSE_ID_PATTERN), courses_views.CoursesGroupsDetail.as_view()),
    url(r'^{0}/groups/*$'.format(COURSE_ID_PATTERN), courses_views.CoursesGroupsList.as_view()),
    url(r'^{0}/overview/*$'.format(COURSE_ID_PATTERN), courses_views.CoursesOverview.as_view()),
    url(r'^{0}/static_tabs/(?P<tab_id>[a-zA-Z0-9_+\/:-]+)$'.format(COURSE_ID_PATTERN), courses_views.CoursesStaticTabsDetail.as_view()),
    url(r'^{0}/static_tabs/*$'.format(COURSE_ID_PATTERN), courses_views.CoursesStaticTabsList.as_view()),
    url(r'^{0}/completions/*$'.format(COURSE_ID_PATTERN), courses_views.CourseModuleCompletionList.as_view(), name='completion-list'),
    url(r'^{0}/projects/*$'.format(COURSE_ID_PATTERN), courses_views.CoursesProjectList.as_view(), name='courseproject-list'),
    url(r'^{0}/metrics/*$'.format(COURSE_ID_PATTERN), courses_views.CoursesMetrics.as_view(), name='course-metrics'),
    url(r'^{0}/time-series-metrics/*$'.format(COURSE_ID_PATTERN), courses_views.CoursesTimeSeriesMetrics.as_view(), name='course-time-series-metrics'),
    url(r'^{0}/metrics/cities/$'.format(COURSE_ID_PATTERN), courses_views.CoursesMetricsCities.as_view(), name='courses-cities-metrics'),
    url(r'^{0}/metrics/completions/leaders/*$'.format(COURSE_ID_PATTERN), courses_views.CoursesMetricsCompletionsLeadersList.as_view(), name='course-metrics-completions-leaders'),
    url(r'^{0}/metrics/grades/*$'.format(COURSE_ID_PATTERN), courses_views.CoursesMetricsGradesList.as_view()),
    url(r'^{0}/metrics/grades/leaders/*$'.format(COURSE_ID_PATTERN), courses_views.CoursesMetricsGradesLeadersList.as_view(), name='course-metrics-grades-leaders'),
    url(r'^{0}/metrics/social/$'.format(COURSE_ID_PATTERN), courses_views.CoursesMetricsSocial.as_view(), name='courses-social-metrics'),
    url(r'^{0}/roles/(?P<role>[a-z_]+)/users/(?P<user_id>[0-9]+)*$'.format(COURSE_ID_PATTERN), courses_views.CoursesRolesUsersDetail.as_view(), name='courses-roles-users-detail'),
    url(r'^{0}/roles/*$'.format(COURSE_ID_PATTERN), courses_views.CoursesRolesList.as_view(), name='courses-roles-list'),
    url(r'^{0}/updates/*$'.format(COURSE_ID_PATTERN), courses_views.CoursesUpdates.as_view()),
    url(r'^{0}/users/(?P<user_id>[0-9]+)$'.format(COURSE_ID_PATTERN), courses_views.CoursesUsersDetail.as_view()),
    url(r'^{0}/users/*$'.format(COURSE_ID_PATTERN), courses_views.CoursesUsersList.as_view()),
    url(r'^{0}/workgroups/*$'.format(COURSE_ID_PATTERN), courses_views.CoursesWorkgroupsList.as_view()),
    url(r'^{0}/navigation/{1}$'.format(COURSE_ID_PATTERN, settings.USAGE_KEY_PATTERN), courses_views.CourseNavView.as_view()),
    url(r'^{0}$'.format(COURSE_ID_PATTERN), courses_views.CoursesDetail.as_view()),
    url(r'/*$^', courses_views.CoursesList.as_view()),
)

urlpatterns = format_suffix_patterns(urlpatterns)
