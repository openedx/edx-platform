from django.conf.urls import url

from .views import dashboard, register_user, login_user

PARTNERS_SLUG_PARAM = '(?P<slug>[0-9a-z_-]+)'

urlpatterns = [
    url(r"^partners/{}/$".format(PARTNERS_SLUG_PARAM),  dashboard, name="partner_url"),
    url(r'^partners/{}/register/$'.format(PARTNERS_SLUG_PARAM), register_user, name="partner_register"),
    url(r'^partners/{}/login/$'.format(PARTNERS_SLUG_PARAM), login_user, name="partner_login"),
]
