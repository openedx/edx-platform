from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^$', views.do_search, name='do_search'),
    url(r'^(?P<course_id>.+)$', views.do_search, name='do_search'),
)
