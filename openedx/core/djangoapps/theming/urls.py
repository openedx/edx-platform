"""
Defines URLs for theming views.
"""

from .helpers import is_comprehensive_theming_enabled
from .views import ThemingAdministrationFragmentView
from django.urls import path

app_name = 'openedx.core.djangoapps.theming'

if is_comprehensive_theming_enabled():
    urlpatterns = [
        path('admin', ThemingAdministrationFragmentView.as_view(),
            name='openedx.theming.update_theme_fragment_view',
        ),
    ]
else:
    urlpatterns = []
