"""
CCX API v0 URLs.
"""


from django.conf import settings
from django.conf.urls import include

from lms.djangoapps.ccx.api.v0 import views
from django.urls import path, re_path

CCX_COURSE_ID_PATTERN = settings.COURSE_ID_PATTERN.replace('course_id', 'ccx_course_id')

CCX_URLS = ([
    path('', views.CCXListView.as_view(), name='list'),
    re_path(fr'^{CCX_COURSE_ID_PATTERN}/?$', views.CCXDetailView.as_view(), name='detail'),
], 'ccx')

app_name = 'v0'
urlpatterns = [
    path('ccx/', include(CCX_URLS)),
]
