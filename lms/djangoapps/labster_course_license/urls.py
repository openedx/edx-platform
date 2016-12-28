"""
URLs for the Labster Course License Feature.
"""
from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(
        r'^labster_license/?$',
        'labster_course_license.views.license_handler', name='labster_license_handler'
    ),
)
