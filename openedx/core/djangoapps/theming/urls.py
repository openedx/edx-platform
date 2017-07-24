"""
Defines URLs for theming views.
"""

from django.conf.urls import url

from .views import ThemingAdministrationFragmentView

urlpatterns = [
    url(
        r'^admin',
        ThemingAdministrationFragmentView.as_view(),
        name='openedx.theming.update_theme_fragment_view',
    ),
]
