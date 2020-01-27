from django.conf.urls import url

from .views import list_specializations

urlpatterns = [
    url(r'^specializations/$', list_specializations, name='list_specializations'),
]
