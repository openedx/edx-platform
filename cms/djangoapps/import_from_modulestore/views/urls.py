"""
Course to Library Import API URLs.
"""

from django.urls import include, path

app_name = 'import_from_modulestore'
urlpatterns = [
    path('v0/', include('cms.djangoapps.import_from_modulestore.views.v0.urls', namespace='v0')),
]
