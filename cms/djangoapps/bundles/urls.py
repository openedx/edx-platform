from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^v0/', include([
        # path(r'^bundle/<uuid:bundle_uuid>/', include([  # <-- once we can use Django 2+, simplify this:
        url(r'^bundle/(?P<bundle_uuid_str>[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12})/', include([
            url(r'^blocks/$', views.bundle_blocks),
        ])),
        url(r'^block/(?P<usage_key_str>gblock-v1:[^/]+)/', include([
            url(r'^$', views.bundle_block),
        ])),
    ])),
]
