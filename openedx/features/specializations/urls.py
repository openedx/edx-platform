from django.conf.urls import url

from .views import list_specializations, specialization_about

urlpatterns = [
    url(r'^specializations/$', list_specializations, name='list_specializations'),
    url(r'^specializations/(?P<specialization_uuid>[0-9a-f]{32})$', specialization_about, name='specialization_about'),
]
