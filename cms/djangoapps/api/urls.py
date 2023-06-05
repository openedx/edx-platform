"""
URLs for the Studio API app
"""


from django.conf.urls import include, url

app_name = 'cms.djangoapps.api'

urlpatterns = [
    url(r'^v1/', include('cms.djangoapps.api.v1.urls', namespace='v1')),
]
