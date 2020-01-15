from django.conf.urls import url

from .views import list_specializations

PARTNERS_SLUG_PARAM = '(?P<slug>[0-9a-z_-]+)'

urlpatterns = [
    # Please keep the `partners/reset_password/` on top
    url(r'^specializations/$', list_specializations, name='list_specializations'),
]
