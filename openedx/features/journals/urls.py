"""
Defines URLs for course bookmarks.
"""

from django.conf.urls import url

from openedx.features.journals.views.marketing import bundle_about
from openedx.features.journals.views import learner_dashboard

urlpatterns = [
    url(r'^bundles/{}/about'.format(r'(?P<bundle_uuid>[0-9a-f-]+)',),
        bundle_about,
        name='openedx.journals.bundle_about'
        ),
    url(r'^$',
        learner_dashboard.journal_listing,
        name='openedx.journals.dashboard'
        ),
]
