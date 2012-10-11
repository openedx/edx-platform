from django.conf.urls import *

urlpatterns = patterns('',
    url(r'^$', 'heartbeat.views.heartbeat', name='heartbeat'),
)
