12. Scope and filter for Third-Party Auth
-----------------------------------------

Status
------

Accepted

Context
-------

The permission class ``ThirdPartyAuthProviderApiPermission`` exists to protect a single view, ``UserMappingView``.  The permission ensures that the OAuth Client Application used during authentication has a related mapping in the ``ProviderApiPermissions`` model for the ``provider_id`` passed to the view.

An example call to this view looks like::

    GET /api/third_party_auth/v0/providers/{provider_id}/users

The problem is that ``ProviderApiPermissions`` has a foreign-key reference to a django-oauth-provider (DOP) table which is no longer supported as of the decision to `Migrate to Django OAuth Toolkit (DOT)`_.

.. _Migrate to Django OAuth Toolkit (DOT): 0002-migrate-to-dot.rst

Decisions
---------

A new scope and filter will be introduced to provide this same Third-Party Auth authorization, and taking advantage of the `More General Scope Filter Support`_ decision.

The new scope and filter are::

    Scope: tpa:read
    Filter: tpa_provider:<provider_id> (e.g. tpa_provider:saml-ubc)

The scope can be protected using the already existing `JwtHasScope`_ DRF permission class in edx-drf-extensions.

The new filter permission class, ``JwtHasTpaProviderFilterForRequestedProvider``, will be implemented in edx-platform to start because it is only used by an edx-platform view, ``UserMappingView``.  Additionally, the permission class is used in conjunction with other legacy permissions and it is simpler to keep all the tests together.

.. _More General Scope Filter Support: 0011-scope-filter-support.rst
.. _JwtHasScope: https://github.com/edx/edx-drf-extensions/blob/64f831d715d14dc2db5a1046201ff14e92fa7c9f/edx_rest_framework_extensions/permissions.py#L70

Consequences
------------

* The django-oauth-provider related model ``ProviderApiPermissions`` can be retired without adding a new model, simplifying our OAuth story.

* The complicated method of handling compound permissions, like `JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS`_ from edx-drf-extensions, needs to be duplicated in edx-platform to properly handle Restricted Applications and ``JwtHasTpaProviderFilterForRequestedProvider``. Simplifying this design is being left to a later decision.

.. _JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS: https://github.com/edx/edx-drf-extensions/blob/64f831d715d14dc2db5a1046201ff14e92fa7c9f/edx_rest_framework_extensions/permissions.py#L171
