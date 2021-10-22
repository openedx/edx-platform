"""
URL definitions for the save_for_later API.
"""


from django.conf.urls import include, url

app_name = 'lms.djangoapps.save_for_later'

urlpatterns = [
    url(r'^v1/', include(('lms.djangoapps.save_for_later.api.v1.urls', 'v1'), namespace='v1')),
]
