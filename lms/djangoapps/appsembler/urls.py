from django.conf.urls import patterns, url

urlpatterns = patterns('appsembler.views',
    url(r'^user$','user_signup_endpoint', name='user_signup_endpoint'),
)