auth_exchange
-------------

Views to support exchange of authentication credentials.
The following are currently implemented:

1. DOTAccessTokenExchangeView

   View for token exchange from 3rd party OAuth access token to 1st party OAuth access token. Uses django-oauth-toolkit (DOT) to manage access tokens.

2. LoginWithAccessTokenView

   1st party (open-edx) OAuth 2.0 access token (bearer/jwt) -> session cookie
