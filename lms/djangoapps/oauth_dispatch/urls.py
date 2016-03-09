"""
OAuth2 wrapper urls
"""

from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt

from . import views


urlpatterns = patterns(
    '',
    # authorize/ URL (below) not yet supported for DOT (MA-2124)
    #url(r'^authorize/?$', login_required(views.AuthorizationView.as_view()), name='capture'),
    url(r'^access_token/?$', csrf_exempt(views.AccessTokenView.as_view()), name='access_token'),
    url(
        r'^exchange_access_token/(?P<backend>[^/]+)/$',
        csrf_exempt(views.AccessTokenExchangeView.as_view()),
        name='exchange_access_token'
    )
)
