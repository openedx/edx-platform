"""
URLs for performance app
"""

from django.conf.urls import url

from openedx.core.djangoapps.performance.views import performance_log

urlpatterns = [
    url(r'^performance$', performance_log),
]
