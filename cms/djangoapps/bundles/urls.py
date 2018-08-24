from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^v0/', include([
        url(r'^bundle/(?P<bundle_slug>[^/]+)/', include([
            url(r'^unit/(?P<olx_path>.+\.olx)$', views.bundle_unit),
        ])),
    ])),
]
