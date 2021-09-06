10. Dealing with Django CSRF Protection in Frontend Apps
--------------------------------------------------------

Status
------

Accepted

Context
-------

For background, please see:

* `Transport JWT in HTTP Cookies`_, where we decided the mechanism that frontend apps will use to authenticate with
  backend API services.

* `Django CSRF Protection`_, which contains a description of Django's CSRF protection.

Frontend apps need a way to obtain a CSRF token when making POST, PUT, and DELETE requests to backend API services
implemented as Django applications with CSRF protection enabled. Each backend service is generally deployed with a CSRF
token cookie scoped to the domain of the given service (ecommerce.edx.org) and named accordingly (ecommerce_csrftoken).
Each backend service uses a unique SECRET_KEY to produce the CSRF token, so a CSRF token created by one service will not
be valid for another service. Therefore, frontend apps served by different subdomains will not have access to these CSRF
token cookies.

.. _Transport JWT in HTTP Cookies: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/docs/decisions/0009-jwt-in-session-cookie.rst
.. _Django CSRF Protection: https://docs.djangoproject.com/en/2.1/ref/csrf/

Decisions
---------

#. **CSRF Token API Endpoint** We will implement an API view that constructs a valid CSRF token and returns
   it in a JSON response. This API view will be added to the `edx-drf-extensions`_ python library under a
   new "csrf" Django app which will be added to INSTALLED_APPS in each backend service as we encounter
   frontend apps that need to make POST, PUT, and DELETE API requests to a given backend service. The CSRF token API
   endpoint will be protected from cross-domain XHR requests using our standard CORS protections (only requests
   originating from pages loaded from one of the domains listed in the CORS_ORIGIN_WHITELIST setting will be
   allowed).

#. **Shared HTTP Client CSRF Token Management Code** We will add code to the `@edx/frontend-auth`_ npm package
   that applies a request interceptor to the Axios HTTP client which will ensure that any POST, PUT, and DELETE
   requests are made with the appropriate CSRF token header. This code will make use of the the CSRF token API
   Endpoint described above to obtain a valid CSRF token for the given backend service for which a request is
   being made.

.. _edx-drf-extensions: https://github.com/edx/edx-drf-extensions
.. _@edx/frontend-auth: https://github.com/edx/frontend-auth

Rejected Alternatives
---------------------

Shared SECRET_KEY Across Backend Services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

One alternative to the solution outlined above would be to share the configured SECRET_KEY setting value
across all backend services and change the CSRF_COOKIE_DOMAIN value to a wildcard off of the second-level
domain of the Open edX installation (e.g. .edx.org). This would allow frontend apps to read the CSRF token
from the cookie that is set when a user logs via the authentication service (currently LMS). Since the
SECRET_KEY value would be shared across all backend services, the frontend would be able to use the same
CSRF token to make POST, PUT, and DELETE API requests to each of these services.

We rejected this alternative due to the fact that it seems more secure to limit the exposure of the SECRET_KEY
value to a single service.

References
----------

* https://fractalideas.com/blog/making-react-and-django-play-well-together-single-page-app-model/
