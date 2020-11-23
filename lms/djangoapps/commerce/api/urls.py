"""
API URLs.
"""


from django.conf.urls import include, url

app_name = 'commerce'
urlpatterns = [
    url(r'^v0/', include('lms.djangoapps.commerce.api.v0.urls')),
    url(r'^v1/', include('lms.djangoapps.commerce.api.v1.urls')),
]
