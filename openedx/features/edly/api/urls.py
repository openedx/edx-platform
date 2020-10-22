from django.conf.urls import include, url

urlpatterns = [
    url('', include('openedx.features.edly.api.v1.urls')),
]
