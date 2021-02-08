from django.conf.urls import url

from .views import dashboard, login_user, performance_dashboard, register_user, reset_password_view

PARTNERS_SLUG_PARAM = '(?P<slug>[0-9a-z_-]+)'

urlpatterns = [
    # Please keep the `partners/reset_password/` on top
    url(r'^partners/reset_password/$', reset_password_view, name='partner_reset_password'),
    url(r'^partners/{}/$'.format(PARTNERS_SLUG_PARAM), dashboard, name='partner_url'),
    url(r'^partners/{}/register/$'.format(PARTNERS_SLUG_PARAM), register_user, name='partner_register'),
    url(r'^partners/{}/login/$'.format(PARTNERS_SLUG_PARAM), login_user, name='partner_login'),
    url(r'^partners/{}/performance/$'.format(PARTNERS_SLUG_PARAM), performance_dashboard, name='partner_performance'),
]
