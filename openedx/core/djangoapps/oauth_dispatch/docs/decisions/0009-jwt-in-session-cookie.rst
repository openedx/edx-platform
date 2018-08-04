9. Transport JWT in Session Cookie
----------------------------------

Status
------

Proposed

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

Note: User authentication for open edX mobile apps is outside the scope of this decision record.

.. _Use JWT as OAuth2 Tokens: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/docs/decisions/0003-use-jwt-as-oauth-tokens-remove-openid-connect.rst
.. _Use Asymmetric JWTs: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/docs/decisions/0008-use-asymmetric-jwts.rst
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

#. **"JWT Cookie".** Upon successful login, the backend login service will create and sign a JWT to identify the
   newly logged in user. The JWT will be embedded in a session cookie ("JWT Cookie"), included in the login
   response and stored in the user's browser cookie jar.

#. **Automatically extract JWT from Cookie on API calls.** The `Django Rest Framework JWT`_ library we use supports a
   JWT_AUTH_COOKIE_ configuration setting to specify the JWT cookie name. When set, the JSONWebTokenAuthentication_
   class `automatically extracts the JWT from the cookie`_. Since all open edX REST endpoints that support JWT-based
   authentication derive from this base class, microfrontends can access them with JWT Cookies. We will enable this
   setting.

.. _Django Rest Framework JWT: https://getblimp.github.io/django-rest-framework-jwt/
.. _JWT_AUTH_COOKIE: https://github.com/GetBlimp/django-rest-framework-jwt/blob/master/docs/index.md#jwt_auth_cookie
.. _JSONWebTokenAuthentication: https://github.com/GetBlimp/django-rest-framework-jwt/blob/0a0bd402ec21fd6b9a5f715d114411836fbb2923/rest_framework_jwt/authentication.py#L71
.. _automatically extracts the JWT from the cookie: https://github.com/GetBlimp/django-rest-framework-jwt/blob/0a0bd402ec21fd6b9a5f715d114411836fbb2923/rest_framework_jwt/authentication.py#L86-L87


JWT Cookie Lifetime
^^^^^^^^^^^^^^^^^^^

#. **Cookie and JWT expiration.** Both the session cookie and the JWT have expiration times.

   * For simplicity and consistency, the session cookie and its containing JWT will expire at the same time. There's
     no need to have these be different values.

   * Given this, JWT cookies will always have expiration values, unlike `current open edX session cookies that may
     have no expiration`_.

   * A configuration setting, JWT_AUTH_COOKIE_EXPIRATION, will specify the expiration duration for JWTs and their
     containing cookie.

#. **Revocation with short-lived JWTs** Given the tradeoff between long-lived JWTs versus immediacy of revocation, we
   need to configure an appropriate expiration value for JWT cookies. In a future world with an API gateway, we can
   have longer lived JWTs with a stateful check against a centralized `JWT blacklist`_ and each JWT uniquely
   identified by a `JWT ID (jti)`_. In the meantime, we will err on the side of security and have short-lived JWTs. 

#. **Refresh JWT Cookies.** When a JWT expires, we do not want to ask the user to login again while their browser
   session remains alive. A microfrontend will detect JWT expiration upon receiving a 401 response from an API
   endpoint. To automatically refresh the JWT cookie, the microfrontend will call a new endpoint ("refresh") that
   returns a new JWT Cookie to keep the user's session alive.

   * To support this, the login endpoint will include 2 related cookies in its response:

     * **JWT Cookie** (as described above), with a *domain* setting so that it is forwarded to any microservice in
       the system.
     * **JWT Refresh Cookie**, with a *domain* setting so that it is sent to the login service only.

#. **Remove JWT Cookie on Logout.** When the user logs out, remove the JWT cookie in the response, which will remove
   it from the user's browser cookie jar. Thus, the user will be logged out of all the application's microfrontends.

.. _`current open edX session cookies that may have no expiration`: https://github.com/edx/edx-platform/blob/92030ea15216a6641c83dd7bb38a9b65112bf31a/common/djangoapps/student/cookies.py#L25-L27
.. _JWT blacklist: https://auth0.com/blog/blacklist-json-web-token-api-keys/
.. _`JWT ID (jti)`: http://self-issued.info/docs/draft-ietf-oauth-json-web-token.html#jtiDef


JWT Cookie Content
^^^^^^^^^^^^^^^^^^

#. **Minimize JWT size.** By `HTTP Cookie RFC standard`_, session cookies need to be `at least 4096 bytes`_. `Modern 
   browsers have remained within this minimum limit`_ and hence do not support more than 4096 bytes. Our current JWT
   size is about 970 bytes (varying with size of user identifiers, like user's name, etc). (Side note: Signing a JWT
   with a 2048 byte asymmetric key increases the JWT's size by 325 bytes.)
   
   To minimize the JWT's size from the start, we should eliminate any unnecessary data that is `currently embedded
   in the JWT`_. For example:

   * *aud* - should remove this since we do not make use of the audience field.
   * *preferred_username* - should be renamed simply to *username*.
   * *administrator* - can keep for now, but may eventually be replaced as *role* data - when we design
     authorization.

.. _HTTP Cookie RFC standard: https://tools.ietf.org/html/rfc6265
.. _at least 4096 bytes: https://tools.ietf.org/html/rfc6265#section-6.1
.. _Modern browsers have remained within this minimum limit: http://browsercookielimits.squawky.net/
.. _currently embedded in the JWT: https://github.com/edx/edx-platform/blob/92030ea15216a6641c83dd7bb38a9b65112bf31a/openedx/core/lib/token_utils.py#L13


JWT Cookie Security
^^^^^^^^^^^^^^^^^^^

#. **Enable CSRF Protection.** Storing JWTs in session cookies will make us potentially vulnerable to CSRF attacks.
   See `JWT Cookie Storage Security`_. To protect against this:
   
   * Enable the HttpOnly_ flag on the cookie, so Javascript code cannot access the cookie directly.
   * Enable the Secure_ flag on the cookie, so it will not be sent (and thus leaked) through an unencrypted channel.
   * Enable `Django's CSRF middleware`_ for every response.
   * Ensure all GET requests are side-effect free, via the `Safe Endpoints middleware`_.
   
     * Note: The `same-origin policy`_ protects against CSRF attacks on GET requests since the rogue website cannot
       access the response from the GET request.
     * However, since the GET request is still processed on the server, we need to ensure there are no unwanted
       side-effects.
     * Question:  If we cannot ensure all GET requests will be side-effect free, can/should we include the CSRF
       value as a GET parameter?

#. **CORS.** `Cross-origin resource sharing (CORS)`_ will need to be configured so that all allowed microfrontends
   can access the necessary backend microservices.

.. _JWT Cookie Storage Security: https://stormpath.com/blog/where-to-store-your-jwts-cookies-vs-html5-web-storage#so-whats-the-difference
.. _HttpOnly: https://www.owasp.org/index.php/HttpOnly
.. _Secure: https://www.owasp.org/index.php/SecureFlag
.. _`Django's CSRF middleware`: https://docs.djangoproject.com/en/1.11/ref/csrf/
.. _Safe Endpoints middleware: https://github.com/edx/edx-platform-private/pull/120
.. _same-origin policy: https://en.wikipedia.org/wiki/Same-origin_policy
.. _Cross-origin resource sharing (CORS): https://en.wikipedia.org/wiki/Cross-origin_resource_sharing


Consequences
------------

#. Instead of storing JWTs in cookies, microfrontends could store them in HTML5 Web Storage. However, that is
   vulnerable to XSS attacks as described in `JWT sessionStorage and localStorage Security`_. Since the open edX 
   system has a stronger security story for CSRF attacks over XSS attacks, we are rejecting this alternative.

#. Since session cookies have a limited size of `at least 4096 bytes`_, we will need to monitor its size increase
   over time and implement a warning before it exceeds the size. Having this hard limit requires us to be judicious
   of what data is included in the JWT. A bloated JWT is not necessarily a benefit to overall web performance.

   If the size limitation becomes a concern in the future, we may need to break up the JWTs into multiple. For
   example, separating authentication-related JWTs from authorization-related JWTs.

.. _JWT sessionStorage and localStorage Security: https://stormpath. com/blog/where-to-store-your-jwts-cookies-vs-html5-web-storage#so-whats-the-difference

References
----------

* https://stormpath.com/blog/where-to-store-your-jwts-cookies-vs-html5-web-storage
* https://dzone.com/articles/cookies-vs-tokens-the-definitive-guide
* http://www.redotheweb.com/2015/11/09/api-security.html
* http://flask-jwt-extended.readthedocs.io/en/latest/tokens_in_cookies.html
