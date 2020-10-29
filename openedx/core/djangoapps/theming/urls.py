"""
Defines URLs for theming views.
"""


from django.conf.urls import url

from .helpers import is_comprehensive_theming_enabled
from .views import ThemingAdministrationFragmentView

app_name = 'openedx.core.djangoapps.theming'

if is_comprehensive_theming_enabled():
    urlpatterns = [
        url(
            r'^admin',
            ThemingAdministrationFragmentView.as_view(),
            name='openedx.theming.update_theme_fragment_view',
        ),
    ]
else:
    urlpatterns = []
