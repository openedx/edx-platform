"""
Courses Structure API v0 URI specification
"""
from django.conf import settings
from django.conf.urls import patterns, url

from course_structure_api.v0 import views


COURSE_ID_PATTERN = settings.COURSE_ID_PATTERN

urlpatterns = patterns(
    '',
    url(r'^courses/$', views.CourseList.as_view(), name='list'),
    url(r'^courses/{}/$'.format(COURSE_ID_PATTERN), views.CourseDetail.as_view(), name='detail'),
    url(r'^course_structures/{}/$'.format(COURSE_ID_PATTERN), views.CourseStructure.as_view(), name='structure'),
    url(
        r'^grading_policies/{}/$'.format(COURSE_ID_PATTERN),
        views.CourseGradingPolicy.as_view(),
        name='grading_policy'
    ),
)

if settings.FEATURES.get('ENABLE_COURSE_BLOCKS_NAVIGATION_API'):
    # TODO (MA-789) This endpoint still needs to be approved by the arch council.
    # TODO (MA-704) This endpoint still needs to be made performant.
    urlpatterns += (
        url(
            r'^courses/{}/blocks/$'.format(COURSE_ID_PATTERN),
            views.CourseBlocksAndNavigation.as_view(),
            {'return_blocks': True, 'return_nav': False},
            name='blocks'
        ),
        url(
            r'^courses/{}/navigation/$'.format(COURSE_ID_PATTERN),
            views.CourseBlocksAndNavigation.as_view(),
            {'return_blocks': False, 'return_nav': True},
            name='navigation'
        ),
        url(
            r'^courses/{}/blocks\+navigation/$'.format(COURSE_ID_PATTERN),
            views.CourseBlocksAndNavigation.as_view(),
            {'return_blocks': True, 'return_nav': True},
            name='blocks+navigation'
        ),
    )
