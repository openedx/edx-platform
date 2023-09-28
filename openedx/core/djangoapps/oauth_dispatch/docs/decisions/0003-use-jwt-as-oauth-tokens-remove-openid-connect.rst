3. Use JWT as OAuth2 Tokens; Remove OpenID Connect
--------------------------------------------------

Status
------

Accepted

Context
-------

The edX system has external OAuth2 client applications, including edX Mobile apps
and external partner services. In addition, there are multiple edX microservices
that are OAuth2 Clients of the LMS.

Some of the internal microservice clients require `OpenID Connect`_ features.
Specifically, they make use of the `ID Token`_ extension to get user profile
details from the LMS via the OAuth protocol. The ID Token can also be forwarded
from one microservice to another, allowing the recipient microservice to
validate the identity of the token's owner without needing to reconnect with a
centralized LMS.

We have integrated our fork of DOP_ with support for OpenID Connect. So, an
access_token request with a DOP client::

    curl -X POST -d "client_id=abc&client_secret=def&grant_type=client_credentials" http://localhost:18000/oauth2/access_token/

includes an id_token field::

    {
        "access_token": <RANDOMLY-GENERATED-ACCESS-TOKEN>,
        "id_token": <BASE64-ENCODED-ID-TOKEN>,
        "expires_in": 31535999,
        "token_type": "Bearer",
        "scope": "profile openid email permissions"
    }

where the value of BASE64-ENCODED-ID-TOKEN decodes to::

    {
        "family_name": "User1",
        "administrator": false,
        "sub": "foo",
        "iss": "http://localhost:18000/oauth2",
        "user_tracking_id": 1234,
        "preferred_username": "user1",
        "name": "User 1",
        "locale": "en",
        "given_name": "User 1",
        "exp": 1516757075,
        "iat": 1516753475,
        "email": "user1@edx.org",
        "aud": "bar"
    }

However, OpenID Connect is a large standard with many features and is not supported by
the DOT_ implementation.

.. _OpenID Connect: http://openid.net/connect/
.. _ID Token: http://openid.net/specs/openid-connect-core-1_0.html#IDToken
.. _DOP: https://github.com/caffeinehit/django-oauth2-provider
.. _DOT: https://github.com/evonove/django-oauth-toolkit

Decision
--------

Remove our dependency on OpenID Connect since we don't really need all its
features and it isn't supported by DOT. Instead, support `JSON Web Token (JWT)`_,
which is a simpler standard and integrates well with the OAuth2 protocol.

.. _JSON Web Token (JWT): https://jwt.io/

The simplest approach is to allow OAuth2 clients to request JWT tokens in place
of randomly generated Bearer tokens. JWT tokens contain user information,
replacing the need for OpenID's ID Tokens altogether.

JWT Token
~~~~~~~~~

JWT tokens will be signed but not encrypted. We will not encrypt them as we
want the requesting Application and relying parties to be able to parse the
JWT for relevant information (like the user's name, etc).

The edX Authorization server (LMS) will selectively include data in the
JWT based on requested scopes (by the Application) and authorized scopes (by
the user). For example:

+--------------------------------+--------------------------+--------------------------------------------+ 
| Application requests Scope     | User authorizes Scope    | Authzn server (LMS) includes in JWT Payload|
+================================+==========================+============================================+
| none                           | n/a                      | - *preferred_username*: user's username    |
|                                |                          | - *sub*: user's anonymous id               |
+--------------------------------+--------------------------+--------------------------------------------+ 
| **'email'**                    | **'email'**              | - *email*: user's email address            |
+--------------------------------+--------------------------+--------------------------------------------+ 
| **'profile'**                  | **'profile'**            | - *name*: user's name in their edX profile |
|                                |                          | - *family_name*: user's last name          |
|                                |                          | - *given_name*: user's first name          |
|                                |                          | - *administrator*: whether user is_staff   |
+--------------------------------+--------------------------+--------------------------------------------+ 
| **'profile'**                  | user does not authorize  | - profile data not provided                |
+--------------------------------+--------------------------+--------------------------------------------+ 

JWT Authentication Library
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the open source `Django Rest Framework JWT library`_ as the backend
implementation for JWT token type authentication.

.. _Django Rest Framework JWT library: https://getblimp.github.io/django-rest-framework-jwt/

Requesting JWT Tokens
~~~~~~~~~~~~~~~~~~~~~

An OAuth2 client requesting a JWT token_type::

    curl -X POST -d "client_id=abc&client_secret=def&grant_type=client_credentials&token_type=jwt" http://localhost:18000/oauth2/access_token/

would now receive::

    {
        "access_token": <BASE64-ENCODED-JWT>,
        "token_type": "JWT",
        "expires_in": 31535999,
        "scope": "read write profile email"
    }

where the value of BASE64-ENCODED-JWT decodes to what the BASE64-ENCODED-ID-TOKEN
decodes to. There would no longer be a separate id_token field, but the
access_token will now contain the data that would have been in the id_token.

**Note:** In order to use the JWT token type to access an API, the Authorization
header needs to specify "JWT" instead of "Bearer"::

    curl -H "Authorization: JWT <BASE64-ENCODED-JWT>" http://localhost:18000/api/user/v1/me

Requesting Bearer Tokens
~~~~~~~~~~~~~~~~~~~~~~~~

OAuth2 Clients that are not interested in receiving JWT tokens may continue to
use the default Bearer token type::

    curl -X POST -d "client_id=abc&client_secret=def&grant_type=client_credentials" http://localhost:18000/oauth2/access_token/

which returns::

    {
        "access_token": <RANDOMLY-GENERATED-ACCESS-TOKEN>,
        "token_type": "Bearer",
        "expires_in": 36000,
        "scope": "read write profile email"
    }

**Note:** In order to use the Bearer token type to access an API, the Authorization
header needs to specify "Bearer"::

    curl -H "Authorization: Bearer <RANDOMLY-GENERATED-ACCESS-TOKEN>" http://localhost:18000/api/user/v1/me

Alternatives
------------

Our implementation of OAuth2+JWT should not be confused with the `IETF standard for
OAuth JWT Assertions`_, which is for a different purpose entirely. It uses JWTs as
a replacement for an assertion_ in the OAuth handshake. That is, it uses the JWT
as a means to *get an OAuth token* (instead of using traditional `OAuth2 grant
types`_, which require *client-secrets* or *passwords*). 

Our implementation, however, returns a JWT *in place of an OAuth token*. The
Authorization server (LMS) creates/signs a JWT that binds information about the
requesting application and the authorizing user. This self-contained token can
then be validated/used by any relying party (microservice/API) for granting access.

If we did eventually support the `IETF standard for OAuth JWT Assertions`_, a client
Application would not send its *client secret* over-the-wire when requesting OAuth
Tokens. Instead, it would use the once out-of-band exchanged *client secret* to sign
its own JWT. This would be a stronger story for authenticating client Application
requests.

.. _IETF standard for OAuth JWT Assertions: https://tools.ietf.org/html/rfc7523#section-2.1
.. _assertion: https://tools.ietf.org/html/rfc7521
.. _OAuth2 grant types: https://tools.ietf.org/html/rfc6749#section-4

Consequences
------------

Pluses
~~~~~~

* The long-term design of the system will be simpler by using simpler
  protocols and frameworks, such as JWT as access tokens.

* OAuth Clients obtain basic identity information within the JWT access
  token without needing to hit an extra user info endpoint.

* Any microservice can validate the JWT as an assertion without making an
  extra round trip to the LMS.

* Although there is no RFC or IETF standard for our use of OAuth+JWT, we
  are using a relatively maintained and used `open source library`_ for our
  implementation.

.. _open source library: https://getblimp.github.io/django-rest-framework-jwt

Minuses
~~~~~~~

* Token invalidation and single Logout become more difficult.

* During the transition period, there will be multiple implementations,
  which may result in confusion and a more complex system. The shorter
  we keep the transition period, the better.
