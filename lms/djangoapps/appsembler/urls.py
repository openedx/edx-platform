from django.conf.urls import patterns, url

urlpatterns = patterns('appsembler.views',
                      url(r'^$','user_signup_endpoint'),
   )