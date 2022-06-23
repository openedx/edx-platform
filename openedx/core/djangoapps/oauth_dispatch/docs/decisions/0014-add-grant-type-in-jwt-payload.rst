14. Added grant type in JWT payload
###################################

Status
------

Accepted

Context
-------

Open edX mobile apps are `migrating to JWT token`_ authentication.
As part of the current mobile authentication flow, we exchange an opaque access token for a session.
This is only allowed for access tokens created with the password grant type.
However, as we migrate from using the opaque access token to a JWT, we are no longer able to determine the grant type of the JWT.

.. _migrating to JWT token: 0013-mobile-migration-to-jwt.rst

Decisions
---------

A new claim ``grant_type`` will be added to the payload while creating the JWT.
The claim ``grant_type`` will be determined using the grant type information stored for the django-oauth-toolkit (DOT) opaque access token that the JWT was based off of during the mobile flow.
JWTs created from an access token in mobile flow will have a grant type of ``password``, and can be used for the session exchange.

Consequences
------------

* JWT will have an additional claim "grant_type" in its payload, which we can use to take decisions regarding auth exchange.
