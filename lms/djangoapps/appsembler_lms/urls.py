from django.conf.urls import patterns, url

urlpatterns = patterns('appsembler_lms.views',
    url(r'^user/$', 'user_signup_endpoint', name='user_signup_endpoint'),
)
