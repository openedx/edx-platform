from django.conf.urls import patterns, url

urlpatterns = patterns('appsembler_cms.views',
    url(r'^course$', 'create_course_endpoint', name='create_course_endpoint'),
)
