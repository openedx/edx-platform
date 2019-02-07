11. Handling Breaking Changes with Major Versions
=================================================

Status
------

Draft

Temporary Implementation Notes
------------------------------

This idea is being put on hold because it is hard to implement.  Here are some notes
about the implementation in case we ever decide to revive this:

JWT Changes:
- sub: changing meaning (does anything care internally?)
- username: must add to scope requested and authorized.  where and how?
- profile: retire? leave alone to shrink our problems?
- copy role out of profile - shouldn't require a major version change.

Places to encapsulate JWT details:
- frontend-auth library
- ... ?
- Note: The fewer pieces of code that care what the JWT looks like, the better.

Django Settings:
    Retire:
    - JWT_SUPPORTED_VERSION
    New:
    - JWT_SUPPORTED_MAJOR_VERSION
        - System-wide setting for requested major version, used in the following places:
            - edx-rest-api-client get access token for server-to-server calls.
            - DOTAccessTokenExchangeView get access token (???)
            - LMS _create_and_set_jwt_cookies
        - Used for rollout. Assumes all backends support new+old major version before switching.
    Future (Never?):
    - JWT_SUPPORTED_VERSIONS
        - Could be added if we ever need config to switch between minor versions.
        - Minor versions should just be additive, and this should not be needed.
        - Doesn't make sense to do this before it is needed.

LMS
- _create_and_set_jwt_cookies (use JWT_SUPPORTED_MAJOR_VERSION)
- AccessTokenView: add support for v=X parameter
- *** create_jwt_for_user (does this need to support multiple versions???)
    - ...

API Gateway
- Who uses this? Do we need to add /oauth2/v2/access_token?
- https://github.com/edx/api-manager/blob/master/swagger/api.yaml#L28

Backend Services
- Rest Client
    - Caller requests access token with major version (use JWT_SUPPORTED_MAJOR_VERSION)
        - Callee needs to support all major versions of token
    - https://github.com/edx/edx-rest-api-client/blob/7ed2a833691d2fdf3a4fbc9189ee5c4443bd892b/edx_rest_api_client/client.py#L68
- DRF Extensions
    - Removing version check
    - https://github.com/edx/edx-drf-extensions/pull/63

DOTAccessTokenExchangeView
- Calls create access token (use JWT_SUPPORTED_MAJOR_VERSION)
- https://github.com/edx/edx-platform/blob/3353e7425e57b8a308318f2feac35c5b0b5dbdaf/openedx/core/djangoapps/auth_exchange/views.py#L109-L114



Context
-------

The ``oauth_dispatch`` urls currently do not support versions. At this time, we would like to have the ability to iterate rapidly while working out details of how the API is called and the resulting payload of the JWT token.

For background, please see:

* `Use JWT as OAuth2 Tokens`_, where we decided to use JWTs for our oAuth2 tokens.

.. _Use JWT as OAuth2 Tokens: 0003-use-jwt-as-oauth-tokens-remove-openid-connect.rst

Decisions
---------

In order to support breaking changes, a major version will be introduced to the ``/access_token`` endpoint to allow the caller to request a particular major version.

The major version will be supplied as a new query parameter. The parameter will look like *?v=N*, where N is the major version (e.g., '1', '2', etc.).

* *Temporarily*, a default version will be allowed.

  * At this time, a default of *v=1* will be assumed if the parameter is not provided.

  * Once v1 is retired, and *v=1* is no longer an acceptable parameter, the parameter should become required and the endpoint should fail if no version is provided. This is consistent with other endpoints where the major version is required as part of the url path, making it more clear that major versions are supported.

Rejected Alternatives
---------------------

Adding Version to the URL Path
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Using the URL path for major versions is documented in the `edX REST API Conventions`_. However, our existing URLs for ``oauth2`` do not support a major version in the URL and are handling routing to both DOT (django-oauth-toolkit) and DOP (django-oauth-provider). See these `oauth2 URL comments in the LMS urls.py`_ for more details. In order to move quickly and avoid the cost of determining how and if the major version could be introduced into the URL path without breaking things, we opted for the simpler solution of adding the query parameter.

.. _edX REST API Conventions: https://openedx.atlassian.net/wiki/spaces/AC/pages/18350757/edX+REST+API+Conventions#edXRESTAPIConventions-6.Version
.. _oauth2 URL comments in the LMS urls.py: https://github.com/edx/edx-platform/blob/f75dff1ec710ad7101a966b22977305370d7abdd/lms/urls.py#L883-L889

