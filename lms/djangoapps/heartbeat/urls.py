from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'heartbeat.views.heartbeat', name='heartbeat'),
)
