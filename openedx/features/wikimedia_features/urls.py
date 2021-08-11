"""
URLs for the Wikimedia Apps
"""


from django.conf.urls import include, url


urlpatterns = [
    url(
        r'^admin_dashboard/',
        include(('openedx.features.wikimedia_features.admin_dashboard.urls',
                 'openedx.features.wikimedia_features.admin_dashboard'), namespace='admin_dashboard')
    ),
]
