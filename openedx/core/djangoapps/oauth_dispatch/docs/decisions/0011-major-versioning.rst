11. Handling Breaking Changes with Major Versions
=================================================

Status
------

Draft

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
