

from django.conf.urls import include, url

app_name = 'entitlements'
urlpatterns = [
    url(r'^v1/', include('entitlements.api.v1.urls')),
]
