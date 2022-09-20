13. Mobile migration to JWT
###########################

Status
------

Accepted

Context
-------

The Open edX mobile apps contain the final usage of the deprecated opaque Bearer access tokens, as documented in the `OAuth2 and Bearer Tokens section of OEP-42 on Authentication`_. Once the mobile apps are no longer using these opaque tokens, BearerAuthentication could be removed through the DEPR process.

Additionally, the Open edX mobile apps plan to add payment features which require calling some ecommerce apis. However, the opaque Bearer access tokens can only be used for authentication and api calls in the lms. As detailed in OEP-42, the JWT access token is the recommended method of authenticating across services.

Until this time, JWT access tokens were not supported for parts of the mobile authentication workflow. Once JWT authentication is enabled for mobile, most of the required apis for the new features already support JWT, and the ones that don't can be easily updated.

.. _OAuth2 and Bearer Tokens section of OEP-42 on Authentication: https://github.com/openedx/open-edx-proposals/blob/6accfc7d5440c9c02f0c17e6ce65c7141af9551f/oeps/best-practices/oep-0042-bp-authentication.rst#oauth2-and-bearer-tokens

Decisions
---------

The mobile apps will migrate its authentication worklflow from using opaque Bearer access tokens to JWT access tokens for authentication, enabling the use of JWTs for cross-service authenticated api calls.

The mobile app currently obtains an edX-issued access token in either of the following ways:

* ``AccessToken View: username/email + password combo with grant_type=password``
* ``AccessTokenExchangeView: 3rd party (social-auth) OAuth 2.0 access token -> 1st party (Open edX) OAuth 2.0 access token``

Additionally, the mobile app can exchange an access token for a session cookie that can be used in a WebView:

* ``LoginWithAccessTokenView: 1st party (Open edX) OAuth 2.0 access token -> session cookie``

The above three endpoints will be updated to also support JWTs. The mobile apps will then use ``JwtAuthentication`` on all the apis they call. Note: almost all the apis already support ``JwtAuthentication``.

Consequences
------------

For migrating the mobile authentication flow from opaque Bearer access tokens to JWTs, the following security risks were identified, and will be mitigated as detailed below:

* Reduce JWT access token expiration.

  * One major difference between JWT and Bearer access tokens is that the JWT is non-revocable. Intentionally, there is no database lookup for a JWT and it is simply trusted if found to be valid.
  * One consequence of this is that a JWT should have a short lifetime in order to limit security risks if the token is hijacked.
  * JWT access token expiration time needs to be configurable separately from the opaque Bearer tokens to enable this change. (Completed as of the writing of this ADR.)

* User Account Status:

  * For 1st-party token exchange for session login using JWTs, it is especially important to ensure that the user account has not been disabled, since the JWT is non-revocable.

* Password Grant Check

  * For the currently proposed 1st-party token exchange for session login using JWTs, we would need an equivalent check to the existing `_is_grant_password` to not expand permissiveness of the endpoint.
  * For resolution, see the `ADR to add grant type in JWT payload`_.

* Asymmetrically Signed JWT

  * We need to check if the JWT was asymmetrically signed by the LMS. We want to ensure that a symmetrically signed JWT, created (signed) by another IDA, could not be compromised and used by an attacker to exchange for a session cookie, which would allow for full compromise of the user.
  * Implementation will involve adding a method to ``edx-drf-extensions`` like ``get_decoded_jwt_from_auth``, but that will decode only asymmetric JWTs.
  * Auth token endpoints that return a JWT will now take a request parameter that will enable Mobile to request asymmetric JWTs. This will enable old symmetric JWTs to continue to work until they are fully deprecated/removed, but enable Mobile to request asymmetric JWTs for this new case where they are required.

.. _ADR to add grant type in JWT payload: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/docs/decisions/0014-add-grant-type-in-jwt-payload.rst
