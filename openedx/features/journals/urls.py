"""
Defines URLs for course bookmarks.
"""

from django.conf.urls import url

from openedx.features.journals.views.marketing import bundle_about

urlpatterns = [
    url(
        r'^$',
        bundle_about,
        name='openedx.journals.bundle_about',
    ),
]
