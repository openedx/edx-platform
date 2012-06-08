from django.conf.urls.defaults import patterns, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^(?P<org>[^/]+)/(?P<course>[^/]+)/calendar/', 'cms.views.calendar', name='calendar'),
    url(r'^accounts/login/', 'instructor.views.do_login', name='login'),
)
