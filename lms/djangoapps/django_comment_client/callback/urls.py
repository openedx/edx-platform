from django.conf.urls.defaults import url, patterns
import django_comment_client.callback.views

urlpatterns = patterns('django_comment_client.callback.views',
    url(r'notifications$', 'notifications_callback', name='notifications_callback'),
)
