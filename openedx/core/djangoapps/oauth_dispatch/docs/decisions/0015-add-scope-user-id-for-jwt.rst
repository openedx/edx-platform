15. Add scope user_id for JWT token
###################################

Status
------

Accepted

Context
-------

JWT tokens are expected to have the ``user_id`` claim, which helps services like e-commerce in identifying the user associated with the token.
The LMS API `to create authentication tokens`_ is used by external organizations to request a token on behalf of their users, mostly using grant_type ``client_credentials`` in the request.
This API is also used by the mobile apps to authenticate end users, using grant_type ``password`` in the request.

Since ``user_id`` is considered sensitive information, It is required that the value be exposed via the API/Token only to end users who can access it by other means.
It is also required that the claim ``user_id`` is present in the JWT token for end users to be identified by systems like e-commerce.

.. _to create authentication tokens: https://github.com/openedx/edx-platform/blob/caf8e456e28f9b9a1f5fa7186d3d155112fb75be/openedx/core/djangoapps/oauth_dispatch/urls.py#L14

Decisions
---------

The scope ``user_id`` will be added to all requests having grant_type ``password`` in the API `/oauth2/access_token/`.


Consequences
------------

The claim ``user_id`` will be present in the JWT token for all requesters who already have access to the login credentials of the user account.
