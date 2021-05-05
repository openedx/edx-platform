auth_exchange
-------------

Views to support exchange of authentication credentials.
The following are currently implemented::

1. AccessTokenExchangeView

   3rd party (social-auth) OAuth 2.0 access token -> 1st party (open-edx) OAuth 2.0 access token
2. LoginWithAccessTokenView

   1st party (open-edx) OAuth 2.0 access token -> session cookie
