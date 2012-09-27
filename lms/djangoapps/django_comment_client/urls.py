from django.conf.urls.defaults import url, patterns, include

urlpatterns = patterns('',
    url(r'', include('django_comment_client.base.urls')),
    url(r'', include('django_comment_client.forum.urls')),
)
