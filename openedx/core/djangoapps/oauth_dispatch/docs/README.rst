OAuth Dispatch App (OAuth2 Provider Interface)
----------------------------------------------

The OAuth Dispatch app is the topmost interface to `OAuth2`_ provider functionality. See decisions_ for its historical journey.

.. _OAuth2: https://tools.ietf.org/html/rfc6749
.. _decisions: decisions/

Background
----------

This section provides a few highlights on the code to provide a high-level perspective on where different aspects of the OAuth2 flow reside. For additional information, see `Open edX Authentication and Authorization`_.

.. _Open edX Authentication and Authorization: https://openedx.atlassian.net/wiki/spaces/PLAT/pages/160912480/Open+edX+Authentication


Provider code
~~~~~~~~~~~~~

* The oauth_dispatch_ app provides the top-most entry points to the OAuth2 Provider views.

  * Its `validator module`_ ensures Restricted Applications only receive expired tokens.

  * Its `Access Token View`_ returns JWTs as access tokens when a JWT token_type is requested.

  * It uses an edX custom JwtBuilder_ implementation to create the JWT.

* The JwtBuilder_ uses the pyjwkest_ library for implementation of `JSON Web Signature (JWS)`_ and other crypto to build and sign JWT tokens.

.. _oauth_dispatch: https://github.com/edx/edx-platform/tree/master/openedx/core/djangoapps/oauth_dispatch
.. _validator module: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/dot_overrides/validators.py
.. _Access Token View: https://github.com/edx/edx-platform/blob/d21a09828072504bc97a2e05883c1241e3a35da9/openedx/core/djangoapps/oauth_dispatch/views.py#L89
.. _JwtBuilder: https://github.com/edx/edx-platform/blob/d21a09828072504bc97a2e05883c1241e3a35da9/openedx/core/lib/token_utils.py#L15
.. _pyjwkest: https://github.com/IdentityPython/pyjwkest
.. _JSON Web Signature (JWS): https://tools.ietf.org/html/draft-ietf-jose-json-web-signature-41

Clients & REST API Clients code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Open edX services, including LMS, use the OAuthAPIClient class from the edx-rest-api-client_ library to make OAuth2 client requests and REST API calls.

Authentication by REST endpoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Recently created edX REST endpoints use the `Django Rest Framework (DRF)`_. The REST endpoint declares which type(s) of authentication it supports or defaults to the *DEFAULT_AUTHENTICATION_CLASSES* value in DRF's *REST_FRAMEWORK* Django setting.

* Open edX REST endpoints that support JWTs as access tokens use JwtAuthentication_ as implemented by the edx-drf-extensions library.

.. _Django Rest Framework (DRF): https://github.com/encode/django-rest-framework
.. _JwtAuthentication: https://github.com/edx/edx-drf-extensions/blob/master/edx_rest_framework_extensions/auth/jwt/README.rst
