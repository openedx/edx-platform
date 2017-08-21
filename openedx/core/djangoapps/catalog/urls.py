from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^management/cache_programs/$', views.cache_programs, name='cache_programs'),
    url(r'^management/cache_programs_test/$', views.cache_programs_test, name='cache_programs_test'),
]
