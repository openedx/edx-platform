from django.conf.urls import url, patterns

urlpatterns = patterns(
    '',

    url(r'^$', 'heartbeat.views.heartbeat', name='heartbeat'),
)
