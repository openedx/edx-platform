from django.conf.urls import url

from .views import list_specializations

urlpatterns = [
    # Please keep the `partners/reset_password/` on top
    url(r'^specializations/$', list_specializations, name='list_specializations'),
]
