from django.conf.urls import url, patterns

urlpatterns = patterns('',  # nopep8
    url(r'^$', 'heartbeat.views.heartbeat', name='heartbeat'),
)
