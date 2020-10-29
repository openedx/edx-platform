"""
URL definitions for api access request API.
"""


from django.conf.urls import include, url

app_name = 'api_admin'
urlpatterns = [
    url(r'^v1/', include('openedx.core.djangoapps.api_admin.api.v1.urls')),
]
