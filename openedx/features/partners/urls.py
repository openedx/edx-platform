from django.conf.urls import url

from .views import dashboard, register_user, reset_password_view

PARTNERS_SLUG_PARAM = '(?P<slug>[0-9a-z_-]+)'

urlpatterns = [
    url(r'^partners/reset_password/$', reset_password_view, name='partner_reset_password'),
    url(r"^partners/{}/$".format(PARTNERS_SLUG_PARAM),  dashboard, name="partner_url"),
    url(r'^partners/{}/register/$'.format(PARTNERS_SLUG_PARAM), register_user, name="partner_register"),
]
