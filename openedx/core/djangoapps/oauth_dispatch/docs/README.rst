OAuth Dispatch App (OAuth2 Provider Interface)
----------------------------------------------

The OAuth Dispatch app is the topmost interface to `OAuth2`_ provider
functionality. See decisions_ for its historical journey.

.. _OAuth2: https://tools.ietf.org/html/rfc6749
.. _decisions: decisions/

Background
----------

This section provides a few highlights on the code to provide a
high-level perspective on where different aspects of the OAuth2 flow
reside. For additional information, see `Open edX Authentication`_.

.. _Open edX Authentication: https://openedx.atlassian.net/wiki/spaces/PLAT/pages/160912480/Open+edX+Authentication

Provider code
~~~~~~~~~~~~~

* The oauth_dispatch_ app provides the top-most entry points to the OAuth2
  Provider views.

  * Its `validator module`_ ensures Restricted Applications only receive expired
    tokens.

  * Its `Access Token View`_ returns JWTs as access tokens when a JWT token_type
    is requested.

  * It uses an edX custom JwtBuilder_ implementation to create the JWT.

* The JwtBuilder_ uses the pyjwkest_ library for implementation of `JSON Web
  Signature (JWS)`_ and other crypto to build and sign JWT tokens.

.. _oauth_dispatch: https://github.com/edx/edx-platform/tree/master/openedx/core/djangoapps/oauth_dispatch
.. _validator module: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/dot_overrides/validators.py
.. _Access Token View: https://github.com/edx/edx-platform/blob/d21a09828072504bc97a2e05883c1241e3a35da9/openedx/core/djangoapps/oauth_dispatch/views.py#L89
.. _JwtBuilder: https://github.com/edx/edx-platform/blob/d21a09828072504bc97a2e05883c1241e3a35da9/openedx/core/lib/token_utils.py#L15
.. _pyjwkest: https://github.com/IdentityPython/pyjwkest
.. _JSON Web Signature (JWS): https://tools.ietf.org/html/draft-ietf-jose-json-web-signature-41

Clients & REST API Clients code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* edX services, including LMS, use the edx-rest-api-client_ library
  to make OAuth2 client requests and REST API calls.

  * Built on top of slumber_, the edx-rest-api-client_ provides
    a utility to retrieve an access token from the LMS. Its Auth_
    classes create appropriate HTTP Authorization headers with
    *Bearer* or *JWT* insertions as needed.

  * It makes use of the PyJWT_ library for cryptographically creating
    JWT tokens.
    
    * **Note:** Creation of JWT tokens in our system should only be done
      by the OAuth Provider. This will break once we use *asymmetric* signing
      keys, for which remote services will not have the private keys.

.. _edx-rest-api-client: https://github.com/edx/edx-rest-api-client
.. _slumber: https://github.com/samgiles/slumber
.. _Auth: https://github.com/edx/edx-rest-api-client/blob/master/edx_rest_api_client/auth.py
.. _PyJWT: https://github.com/jpadilla/pyjwt

Authentication by REST endpoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Recently created edX REST endpoints use the `Django Rest Framework (DRF)`_.
  The REST endpoint declares which type(s) of authentication it supports
  or defaults to the *DEFAULT_AUTHENTICATION_CLASSES* value in DRF's 
  *REST_FRAMEWORK* Django setting.

* edX REST endpoints that support JWTs as access tokens declare the custom
  edX JwtAuthentication_ class in its DRF authentication_classes_ scheme.

  * JwtAuthentication_ is implemented in the edx-drf-extensions_ library.

  * JwtAuthentication_ extends the JSONWebTokenAuthentication_ class
    implemented in the django-rest-framework-jwt_ library.

  * JwtAuthentication_ is used to authenticate an API request only
    if it is listed in the endpoint's authentication_classes_ and the
    request's Authorization header specifies "JWT" instead of "Bearer".

  * **Note:** The Credentials service has its own implementation of 
    JwtAuthentication_ and should be converted to use the common
    implementation in edx-drf-extensions_.

* **Note:** There is also an auth-backends_ repo that should eventually
  go away once Open ID Connect is no longer used. The only remaining
  user of its EdXOpenIdConnect_ class is the edx-analytics-dashboard_.

.. _Django Rest Framework (DRF): https://github.com/encode/django-rest-framework
.. _JwtAuthentication: https://github.com/edx/edx-drf-extensions/blob/4569b9bf7e54a917d4acdd545b10c058c960dd1a/edx_rest_framework_extensions/auth/jwt/authentication.py#L17
.. _authentication_classes: http://www.django-rest-framework.org/api-guide/authentication/#setting-the-authentication-scheme
.. _edx-drf-extensions: https://github.com/edx/edx-drf-extensions
.. _django-rest-framework-jwt: https://github.com/GetBlimp/django-rest-framework-jwt
.. _JSONWebTokenAuthentication: https://github.com/GetBlimp/django-rest-framework-jwt/blob/0a0bd402ec21fd6b9a5f715d114411836fbb2923/rest_framework_jwt/authentication.py#L71
.. _auth-backends: https://github.com/edx/auth-backends
.. _EdXOpenIdConnect: https://github.com/edx/auth-backends/blob/31c944289da0eec7148279d7ada61553dbb61f9e/auth_backends/backends.py#L63
.. _edx-analytics-dashboard: https://github.com/edx/edx-analytics-dashboard
