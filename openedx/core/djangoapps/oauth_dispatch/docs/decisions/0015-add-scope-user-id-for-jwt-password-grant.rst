15. Add scope user_id for JWT token for grant_type password
###########################################################

Status
------

Accepted

Context
-------

In Feb 2018, to enable analytics (Segment) from Microfrontends (MFEs), a ``user_id`` claim was added to the JWT token `in this PR<https://github.com/openedx/edx-platform/pull/19765>`__.

The LMS API `to create authentication tokens`_ is used by external organizations to request a token on behalf of their users, mostly using grant_type ``client_credentials`` in the request. Since ``user_id`` is considered sensitive information, especially when combined with email and username which were already available in the JWT, it was decided to only add the ``user_id`` claim when a ``user_id`` scope was supplied. All MFE JWT cookies, which are known to only be used directly by the user, automatically used the ``user_id`` scope in order to get the required ``user_id`` claim.

No ADR could be found for the Feb 2018 decision detailed above.

In June 2019, an `ADR was captured in ecommerce`_ around the requirements to have the LMS user_id available for requests to ecommerce.

In 2022, the mobile apps switched to using JWTs for authentication. However, these JWTs were missing the ``user_id`` scope and claim required by the ecommerce service.

.. _to create authentication tokens: https://github.com/openedx/edx-platform/blob/caf8e456e28f9b9a1f5fa7186d3d155112fb75be/openedx/core/djangoapps/oauth_dispatch/urls.py#L14
.. _ADR was captured in ecommerce: https://github.com/openedx/ecommerce/blob/master/docs/decisions/0004-unique-identifier-for-users.rst

Decisions
---------

- The original decision to add the ``user_id`` claim to the JWT token using the ``user_id`` scope has been captured in the context of this ADR, because no ADR could be found.
- The scope ``user_id`` will be added to all requests having grant_type ``password`` in the API `/oauth2/access_token/`.

Consequences
------------

- The claim ``user_id`` will be present in the JWT token for all requesters who already have access to the login credentials of the user account.
- The ``user_id`` scope will continue to protect other JWT requests that don't require this sensitive information.
- This pattern could potentially be used to clean-up the manually added ``user_id`` scope for oauth clients involved in the social auth flow in the future.
