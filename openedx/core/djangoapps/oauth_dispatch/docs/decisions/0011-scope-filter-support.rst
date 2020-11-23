11. More General Scope Filter Support
-------------------------------------

Status
------

Accepted

Context
-------

For background, please see:

* `Include Organizations in Tokens`_, where we decided to include a `content_org` filter in JWT tokens.

The implementation of the `content_org` filter included a new model for relating OAuth Applications and Organizations. This design made it difficult to add new types of filters, especially if they weren't tied to organizations.

Decisions
---------

#. **Add ApplicationAccess filters** Add a ``filters`` field to the ApplicationAccess model to more quickly allow for new filter types.

#. **Remove ApplicationOrganization** Deprecate and remove the ApplicationOrganization model which could only handle a very small subset of filters.

Consequences
------------

* Adding the `filters` field to the ApplicationAccess model allows for a simpler design with the following benefits:

  * This enables filters, which typically have some relationship to scopes, to be defined in the same admin screen. This should make it simpler to define oAuth Applications with proper security.

  * This enables the removal of the separate ApplicationOrganization model, which was more complex to configure and less clear regarding its impact on the JWT.

*. The new `filters` field must be added to the EdxOAuth2AuthorizationView_ to handle user authorization for OAuth Applications with grant type 'Authorization code'. This work will be done in a future PR detailed in BOM-1291_.

Using the example from `Include Organizations in Tokens`_, we would now simply use the Application Access admin screen to set::

  Scopes: grades:read,enrollments:read
  Filters: content_org:Microsoft

This would result in a JWT that contains the following, assuming these two scopes were requested::

  {
    "scopes": ["grades:read", "enrollments:read"],
    "filters": ["content_org:Microsoft", "user:me"],
    ...
  }

Note: Every JWT access token created using a given OAuth Application will include **all filters** defined for that application. This was also true as of the initial introduction of filters.

.. _EdxOAuth2AuthorizationView: https://github.com/edx/edx-platform/blob/9cf2f9f298e5e8be3b3abcaadaf0b7a96d0de0df/openedx/core/djangoapps/oauth_dispatch/dot_overrides/views.py#L16
.. _BOM-1291: https://openedx.atlassian.net/browse/BOM-1291
.. _Transport JWT in HTTP Cookies: 0007-include-organizations-in-tokens.rst
