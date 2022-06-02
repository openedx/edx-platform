12. Added grant type in JWT payload
-----------------------------------------

Status
------

Accepted

Context
-------

Edx mobile apps are `migrating from Dot access token to JWT token`_ authentication.Therefore gradually adding JWT support in required APIS.
To exchange JWT with session cookies we need to determine the grant type of the access token first.
We are already doing this in ``/oauth2/login`` view for dot access token, but we don't have grant type in JWT.

.. _migrating from Dot access token to JWT token: https://2u-internal.atlassian.net/browse/LEARNER-8481

Decisions
---------

A new key ``grant_type`` will be added in payload while creating JWT. Key ``grant_type`` will be determined through dot access token for mobile flow.
Since we create JWT from access token in mobile flow therefore its value will be ``password``. We can provide any value other than password and by default it will be an empty string.

Consequences
------------

* JWT will have an additional attribute i.e. grant_type in its payload, which we can use to take decisions regarding auth exchange.
