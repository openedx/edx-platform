5. Restricted Application for SSO
---------------------------------

Status
------

Partially Replaced (see ADR `Enforce Scopes in LMS APIs`_)

.. _Enforce Scopes in LMS APIs: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/docs/decisions/0006-enforce-scopes-in-LMS-APIs.rst#3-restricted-applications-receive-unexpired-jwts-signed-with-a-new-key

Context
-------

External edX clients would like to use edX as an Identity Provider and verify
the edX identity of a user. The OAuth2 protocol's Authorization Code grant type
already supports this behavior and our OAuth2 clients can use it for this
purpose. However, we want to issue *scoped* access tokens to external edX 
clients so end users can limit what API calls the clients make on their behalf.

The OAuth2 standard for controlling the use of access tokens is `Access Token
Scopes`_. With Scopes, an end user explicitly authorizes the actions that an
OAuth2 client is allowed to perform with the issued access token. Scopes
allow us to support SSO and issue access tokens on behalf of users, knowing
the users have approved the usage of the tokens. 

However, the edX platform has not enabled wider usage of Scopes by API
endpoints, beyond the basic values of 'email' and 'profile'. It would be a
major undertaking to update all of our microservices to fully support Scopes,
while keeping the system up and running.

.. _Access Token Scopes: https://tools.ietf.org/html/rfc6749#section-3.3

Decision
--------

Implement a new model in oauth_dispatch to selectively designate DOT Applications
as "Restricted Applications". For those external clients that want SSO capability
with edX as an Identity Provider, configure them as a "Restricted Application".
Although these applications can still request access tokens via the usual
Authorization Code grant protocol, issue them only **expired** access tokens
so they cannot make unauthorized calls to our API endpoints.

.. note::
    Although we still use the new model for "Restricted Applications", the decision to use **expired** access tokens has been superseded by ADR `Enforce Scopes in LMS APIs`_. That ADR specifies a different method to restrict "Restricted Applications" from accessing API endpoints that have not implemented Scopes.

Consequences
------------

Pluses
~~~~~~

* It is a minimal effort to introduce a new "Restricted Application" model
  and update the oauth_dispatch logic to create expired tokens.

* SSO OAuth2 clients can now verify the identity of edX users when they 
  successfully receive an OAuth2 access token in the Authorization Code grant
  type handshake.

* If they make the access token request with token_type=jwt, they receive
  a JSON Web Token (JWT) with basic information about the user's identity,
  including their username and edX Anonymous ID.

* If they include 'email' scope in their authorization request and the user
  approves, the JWT will include the user's email address as well.

* If they include 'profile' scope in their authorization request and the user
  approves, the JWT will include the user's full name and whether they have
  staff access.

Minuses
~~~~~~~

* Returning expired tokens adds additional technical debt on top of the
  debt incurred by not implementing scopes.
