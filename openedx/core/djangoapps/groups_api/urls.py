"""
URLs for the groups REST API app.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from django.conf.urls import include, url
from rest_framework import routers

from openedx.core.djangoapps.groups_api import views


router = routers.SimpleRouter()
router.register(r'groups', views.GroupViewSet, 'group')

app_name = 'groups_api'
urlpatterns = [
    url(r'^v1/', include(router.urls)),
]
