"""
Django URLs for service status app
"""

from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(
        r'^$',
        'program_marketing.views.explore_programs',
        name='explore_programs'
    ),
)
