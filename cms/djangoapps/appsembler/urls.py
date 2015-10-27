from django.conf.urls import patterns, url

urlpatterns = patterns('cms.djangoapps.appsembler.views',
    url(r'^course$','create_course_endpoint'),
)