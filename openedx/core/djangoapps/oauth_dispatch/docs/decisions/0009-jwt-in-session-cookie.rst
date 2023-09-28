9. Transport JWT in HTTP Cookies
--------------------------------

Status
------

Accepted

Context
-------

For background, please see:

* `Use JWT as OAuth2 Tokens`_, where we decided to use JSON Web Tokens (JWTs) as OAuth2 access tokens, thereby
  embedding user identification information in access tokens.

* `Use Asymmetric JWTs`_, where we decided to sign JWTs with public-private keypairs, thereby enabling less trusted
  3rd parties to receive and verify JWTs (with published signing public keys).


These earlier decisions have focused on the authentication needs of backend services for their connections and API
requests. Those services use traditional OAuth2 grant types (Credentials and Authorization Code) and obtain JWTs for
making API requests - as described in `Use JWT as OAuth2 Tokens`_.

Moving forward, we need a simple and easy-to-use authentication mechanism for frontend applications as well. As
described in `Decoupled Frontend Architecture`_, each individual `microfrontend`_ supports its own use case. As a
user interacts with the overall application, the user's experience may lead them through multiple microfrontends,
each accessing APIs on various backends. Stateless authentication (via self-contained JWTs) would allow scalable
interactions between microfrontends and microservices.

Note: User authentication for open edX mobile apps is outside the scope of this decision record. As a brief note, we
believe any decisions in this record will neither affect the current authentication mechanisms used for mobile
apps nor impact forward compatibility when/if mobile apps are consolidated to use a similar (if not the same)
authentication mechanism as outlined here for web apps.

.. _Use JWT as OAuth2 Tokens: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/docs/decisions/0003-use-jwt-as-oauth-tokens-remove-openid-connect.rst
.. _Use Asymmetric JWTs: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/docs/decisions/0008-use-asymmetric-jwts.rst
.. _Decoupled Frontend Architecture: https://openedx.atlassian.net/wiki/spaces/FEDX/pages/790692200/Decoupled+Frontend+Architecture
.. _microfrontend: https://micro-frontends.org/

Decisions
---------

Login -> Cookie -> API
^^^^^^^^^^^^^^^^^^^^^^

#. **Single Login Microfrontend and Microservice.** There will be only a single microfrontend and a corresponding
   single (backend) microservice (currently LMS) from which users can login to the edX system. This will isolate any
   login-related vulnerabilities (i.e., frontend applications that gain access to users' passwords) and
   login-related protections (i.e., password validation policies) to single points in the system.

#. **"Two JWT Cookies".** Upon successful login, the backend login service will create and sign a JWT to identify the
   newly logged in user. The JWT will be divided into the following 2 HTTP cookies (inspired by `Lightrail's
   design`_), included in the login response, and stored in the user's browser cookie jar:

   * **"JWT Header/Payload Cookie"**
     * Contains only the header and payload portions of the JWT.
     * Disable HTTPOnly_ so the microfrontend can access user/role data in the JWT payload.

   * **"JWT Signature Cookie"**
     * Contains only the public key signature portion of the JWT.
     * Enable HTTPOnly_ so the signature is unavailable to JS code. See `JWT Cookie Security`_ below.

#. **Automatically recombine and extract the JWT from Cookies on API calls.**
     * A new middleware JwtAuthCookieMiddleware will reconstitute the divided JWT from its two cookies and store the
       recombined JWT in a temporary cookie specified by JWT_AUTH_COOKIE_.
     * The `Django Rest Framework JWT`_ library we use makes use of the JWT_AUTH_COOKIE_ configuration setting.
       When set, the JSONWebTokenAuthentication_ class `automatically extracts the JWT from the cookie`_. Since all
       open edX REST endpoints that support JWT-based authentication derive from this base class, their authentication
       checks will make use of the JWTs provided in the JWT-related cookies.

#. **Introduce HTTP_USE_JWT_COOKIE header for backward compatibility and rollout.**
     * As we incrementally add JWTAuthentication throughout all backend microservices and APIs, we will need to support
       multiple authentication mechanisms for a period of time. Once JWT cookies are enabled and automatically sent with
       every (post-Login) AJAX request from the browser, backend APIs will try to authenticate the request with the
       sent JWT cookies.
     * The cookies are sent regardless of whether the request comes from an updated microfrontend or from a legacy
       server-side rendered UI. However, since only updated microfrontends will have the logic to refresh JWT cookies
       (see "Refresh JWT Cookies" below), older frontends will not handle expired JWT cookies and so will run into 401
       failures.
     * To prevent this issue, we will introduce a new HTTP header called "HTTP_USE_JWT_COOKIE" that will be selectively
       set only by microfrontends that want to use JWT cookie based authentication. The new middleware will check for
       this header before trying to reconstitute and use the JWT token.
     * Additionally, select login-required APIs can be updated to redirect the caller to the Login page when the JWT
       expires. This can be accomplished by enabling `JwtRedirectToLoginIfUnauthenticatedMiddleware`_ in the Django
       service and updating the API to require the `LoginRedirectIfUnauthenticated`_ permission class. The middleware
       automatically sets "HTTP_USE_JWT_COOKIE" for incoming requests to APIs that require the
       `LoginRedirectIfUnauthenticated`_ permission.

.. _`Lightrail's design`: https://medium.com/lightrail/getting-token-authentication-right-in-a-stateless-single-page-application-57d0c6474e3
.. _Django Rest Framework JWT: https://getblimp.github.io/django-rest-framework-jwt/
.. _JWT_AUTH_COOKIE: https://github.com/GetBlimp/django-rest-framework-jwt/blob/master/docs/index.md#jwt_auth_cookie
.. _JSONWebTokenAuthentication: https://github.com/GetBlimp/django-rest-framework-jwt/blob/0a0bd402ec21fd6b9a5f715d114411836fbb2923/rest_framework_jwt/authentication.py#L71
.. _automatically extracts the JWT from the cookie: https://github.com/GetBlimp/django-rest-framework-jwt/blob/0a0bd402ec21fd6b9a5f715d114411836fbb2923/rest_framework_jwt/authentication.py#L86-L87
.. _JwtRedirectToLoginIfUnauthenticatedMiddleware: https://github.com/openedx/edx-drf-extensions/blob/0351010f1836e4cebd6bdc757d477b2f56265b17/edx_rest_framework_extensions/auth/jwt/middleware.py#L76
.. _LoginRedirectIfUnauthenticated: https://github.com/openedx/edx-drf-extensions/blob/0351010f1836e4cebd6bdc757d477b2f56265b17/edx_rest_framework_extensions/permissions.py#L147


JWT Cookie Lifetime
^^^^^^^^^^^^^^^^^^^

#. **Cookie and JWT expiration.** Both the HTTP cookies and the JWT have expiration times.

   * For simplicity and consistency, the cookies and their containing JWT will expire at the same time. There's
     no need to have these be different values.

   * Given this, JWT cookies will always have expiration values, unlike `current open edX session cookies that may
     have no expiration`_.

   * A configuration setting, JWT_AUTH_COOKIE_EXPIRATION, will specify the expiration duration for JWTs and their
     containing cookie.

#. **Revocation with short-lived JWTs** Given the tradeoff between long-lived JWTs versus immediacy of revocation, we
   need to configure an appropriate expiration value for JWT cookies. In a future world with an API gateway, we *may*
   have longer lived JWTs with a *stateful* check against a centralized `JWT blacklist`_ and each JWT uniquely
   identified by a `JWT ID (jti)`_. In the meantime, we will err on the side of security and have short-lived JWTs.

#. **Refresh JWT Cookies.** When a JWT expires, we do not want to ask the user to login again while their browser
   session remains alive. A microfrontend will detect JWT expiration upon receiving a 401 response from an API
   endpoint, or preemptively recognize an imminent expiration. To automatically refresh the JWT cookie, the
   microfrontend will call a new endpoint ("refresh") that returns a new JWT Cookie to keep the user's session alive.

#. **Remove JWT Cookie on Logout.** When the user logs out, we will remove all JWT-related cookies in the response,
   which will remove them from the user's browser cookie jar. Thus, the user will be logged out of all the
   microfrontends.

.. _`current open edX session cookies that may have no expiration`: https://github.com/openedx/edx-platform/blob/92030ea15216a6641c83dd7bb38a9b65112bf31a/common/djangoapps/student/cookies.py#L25-L27
.. _JWT blacklist: https://auth0.com/blog/blacklist-json-web-token-api-keys/
.. _`JWT ID (jti)`: http://self-issued.info/docs/draft-ietf-oauth-json-web-token.html#jtiDef


JWT Cookie Content
^^^^^^^^^^^^^^^^^^

#. **Minimize JWT size.** According to the `HTTP Cookie RFC standard`_, HTTP cookies `up to 4096 bytes`_ should be
   supported by a browser. `Modern browsers have treated this requirement as a maximum`_ - and hence do not support
   more than 4096 bytes. Our current JWT size is about 970 bytes (varying with size of user identifiers, like user's
   name, etc). (Side note: Signing a JWT with a 2048 byte asymmetric key increases the JWT's size by 325 bytes.)

   To minimize the JWT's size from the start, we should eliminate any unnecessary data that is `currently embedded
   in the JWT`_. For example:

   * *aud* - should remove this since we do not make use of the audience field.
   * *preferred_username* - should be renamed simply to *username*.
   * *administrator* - can keep for now, but may eventually be replaced as *role* data - when we design
     authorization.

.. _HTTP Cookie RFC standard: https://tools.ietf.org/html/rfc6265
.. _up to 4096 bytes: https://tools.ietf.org/html/rfc6265#section-6.1
.. _Modern browsers have treated this requirement as a maximum: http://browsercookielimits.squawky.net/
.. _currently embedded in the JWT: https://github.com/openedx/edx-platform/blob/92030ea15216a6641c83dd7bb38a9b65112bf31a/openedx/core/lib/token_utils.py#L13


JWT Cookie Security
^^^^^^^^^^^^^^^^^^^

#. **Enable CSRF Protection.** Storing JWTs in HTTP cookies is potentially vulnerable to CSRF attacks.
   See `JWT Cookie Storage Security`_. To protect against this:

   * Enable the HttpOnly_ flag on the **"JWT Signature Cookie"**, so Javascript code cannot misuse the JWT.
   * Enable the Secure_ flag on the cookie, so it will not be sent (and thus leaked) through an unencrypted channel.
   * Enable `Django's CSRF middleware`_ for every response.
   * Ensure all GET requests are side-effect free.

     * Note: The `same-origin policy`_ protects against CSRF attacks on GET requests since the rogue website cannot
       access the response from the GET request.
     * However, even though the rogue website cannot access the response, the GET request is still processed on the
       server before returning the response. So we need to ensure there are no unwanted side-effects on the server.

#. **CORS and withCredentials.** `Cross-origin resource sharing (CORS)`_ will need to be configured so that all allowed
   microfrontends can access the necessary backend microservices. In addition, microfrontends will need to set the
   withCredentials_ attribute so that the JWT Cookie gets sent when API calls are made.

   Note: We cannot selectively choose which cookies are sent so all edX-issued cookies will be sent with these API
   calls. Apparently, we already send all edX cookies on API requests today, so this will not cause a significant
   performance issue.


.. _JWT Cookie Storage Security: https://stormpath.com/blog/where-to-store-your-jwts-cookies-vs-html5-web-storage#so-whats-the-difference
.. _HttpOnly: https://www.owasp.org/index.php/HttpOnly
.. _Secure: https://www.owasp.org/index.php/SecureFlag
.. _`Django's CSRF middleware`: https://docs.djangoproject.com/en/1.11/ref/csrf/
.. _same-origin policy: https://en.wikipedia.org/wiki/Same-origin_policy
.. _Cross-origin resource sharing (CORS): https://en.wikipedia.org/wiki/Cross-origin_resource_sharing
.. _withCredentials: https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/withCredentials


Consequences
------------

#. Since HTTP cookies have a limited size of `at least 4096 bytes`_, we will need to monitor its size increase
   over time and implement a warning before it exceeds the size. Having this hard limit requires us to be judicious
   of what data is included in the JWT. A bloated JWT is not necessarily a benefit to overall web performance.

   Separating the JWT into two, specifically its large signature, mitigates this issue significantly.

#. Rejected Alternative: Instead of storing JWTs in cookies, microfrontends could store them in HTML5 Web Storage.
   However, that is vulnerable to XSS attacks as described in `JWT sessionStorage and localStorage Security`_.

#. Since the **"JWT Header/Payload Cookie"** is accessible to the microfrontend JS code, it allows the microfrontend
   to get user information directly and immediately from the cookie.

   We rejected the following alternatives for accessing this user information:

   #. Add an extra round trip to get the user-data from a backend API, and then cache it in HTML5 Storage.
   #. Continue to use and expand the current `JS-accessible user-info cookie`_, which contains user-data.
   #. Have the server populate the initial DOM with this data, but this would only work for server-generated HTML.

.. _at least 4096 bytes: http://browsercookielimits.squawky.net/
.. _JWT sessionStorage and localStorage Security: https://stormpath. com/blog/where-to-store-your-jwts-cookies-vs-html5-web-storage#so-whats-the-difference
.. _JS-accessible user-info cookie: https://github.com/openedx/edx-platform/blob/70d1ca474012b89e4c7184d25499eb87b3135409/common/djangoapps/student/cookies.py#L151

References
----------

* https://stormpath.com/blog/where-to-store-your-jwts-cookies-vs-html5-web-storage
* https://dzone.com/articles/cookies-vs-tokens-the-definitive-guide
* http://www.redotheweb.com/2015/11/09/api-security.html
* http://flask-jwt-extended.readthedocs.io/en/latest/tokens_in_cookies.html
* https://medium.com/lightrail/getting-token-authentication-right-in-a-stateless-single-page-application-57d0c6474e3
