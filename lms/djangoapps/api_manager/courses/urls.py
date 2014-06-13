"""
Courses API URI specification
The order of the URIs really matters here, due to the slash characters present in the identifiers
"""
from django.conf.urls import patterns, url

from rest_framework.urlpatterns import format_suffix_patterns

from api_manager.courses import views as courses_views

urlpatterns = patterns(
    '',
    url(r'/*$^', courses_views.CoursesList.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)$', courses_views.CoursesDetail.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/content/(?P<content_id>[a-zA-Z0-9/_:]+)/groups/(?P<group_id>[0-9]+)$', courses_views.CourseContentGroupsDetail.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/content/(?P<content_id>[a-zA-Z0-9/_:]+)/groups/*$', courses_views.CourseContentGroupsList.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/content/(?P<content_id>[a-zA-Z0-9/_:]+)/children/*$', courses_views.CourseContentList.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/content/(?P<content_id>[a-zA-Z0-9/_:]+)/users/*$', courses_views.CourseContentUsersList.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/content/(?P<content_id>[a-zA-Z0-9/_:]+)$', courses_views.CourseContentDetail.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/content/*$', courses_views.CourseContentList.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/grades/*$', courses_views.CoursesGradesList.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/groups/(?P<group_id>[0-9]+)$', courses_views.CoursesGroupsDetail.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/groups/*$', courses_views.CoursesGroupsList.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/overview/*$', courses_views.CoursesOverview.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/updates/*$', courses_views.CoursesUpdates.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/static_tabs/(?P<tab_id>[a-zA-Z0-9/_:]+)$', courses_views.CoursesStaticTabsDetail.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/static_tabs/*$', courses_views.CoursesStaticTabsList.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/users/(?P<user_id>[0-9]+)$', courses_views.CoursesUsersDetail.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/users/*$', courses_views.CoursesUsersList.as_view()),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/completions/*$', courses_views.CourseModuleCompletionList.as_view(), name='completion-list'),
)

urlpatterns = format_suffix_patterns(urlpatterns)
