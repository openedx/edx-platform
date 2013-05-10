from django.conf.urls import *

urlpatterns = patterns('',  # nopep8
    url(r'^$', 'heartbeat.views.heartbeat', name='heartbeat'),
)
