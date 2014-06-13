from django.conf.urls import url, patterns, include

urlpatterns = patterns('',  # nopep8
    url(r'forum/?', include('django_comment_client.forum.urls')),
    url(r'', include('django_comment_client.base.urls')),
)
