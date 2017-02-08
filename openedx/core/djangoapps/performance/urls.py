"""
URLs for performance app
"""

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'openedx.core.djangoapps.performance.views',

    url(r'^performance$', 'performance_log'),
)
