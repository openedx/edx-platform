from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^management/cache_programs/$', views.cache_programs, name='cache_programs'),
]
