from django.conf.urls import url

from .views import dashboard

urlpatterns = [
    url(r"^partner/(?P<slug>[0-9a-z_-]+)/$",  dashboard, name="partner_url"),
]
