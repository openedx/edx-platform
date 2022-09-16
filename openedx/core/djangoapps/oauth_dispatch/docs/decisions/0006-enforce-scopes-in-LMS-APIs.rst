6. Enforce Scopes in LMS APIs
-----------------------------

Status
------

Accepted

Context
-------

Although external edX clients, as Restricted Applications, can use edX
as an Identity Provider, they cannot successfully make any API calls on
behalf of users. As explained in 0005-restricted-application-for-SSO_,
edX prevents successful API calls since our API endpoints do not enforce
OAuth scopes.

For additional background information on the current implementation,
see the README_.

.. _0005-restricted-application-for-SSO: 0005-restricted-application-for-SSO.rst
.. _README: ../README.rst

Decisions
---------

Add support for enforcing OAuth2 scopes by making the following advancements
simultaneously.

1. Define and configure new OAuth2 Scopes for accessing API resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* For now, we will start with an initial set of OAuth2 Scopes based on
  immediate API needs. See 0007-include-organizations-in-tokens_ for
  initial examples.

* OAuth2 clients should be frugal about limiting the scopes they request
  in order to:

  * keep the data payload small
  * keep the UX of the user approval form reasonable
  * follow principle of least privilege

2. Add a version number in the OAuth2 token payload
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As a preemptive step, set a version number field (= 1) in the OAuth2 token
payload.

3. Restricted Applications receive *unexpired* JWTs, signed with a *new key*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We will no longer return expired *JWTs as access tokens* to Restricted
Applications. We will sign them with a *new key* that is not shared with
unprotected microservices.

* API endpoints that are exposed by other microservices and that
  support OAuth2 requests are vulnerable to exploitation until
  they are also updated to enforce scopes.

  * We do not want a lock-step deployment across all of our microservices.
    We want to enable these changes without blocking on updating all
    microservices.

  * We do not want to issue unexpired *Bearer tokens* to Restricted
    Applications since they will be accepted by unprotected microservices.
    There's no way to retroactively inform existing microservices
    to reject scope-limiting *Bearer tokens*.

* On the other hand, existing unprotected microservices will reject
  *JWT tokens* signed with new keys that they do not know about. We will
  make the new keys available to a microservice only after they
  have been updated to enforce OAuth Scopes.

  * The `edx-platform settings`_ will be updated to support a new signing
    key. Since this transition to using a new key will happen as a staged
    rollout, we will take this opportunity to have the new signing key be
    an asymmetric key, rather than the current (not as secure) shared
    symmetric key.

  * oauth_dispatch.views.AccessTokenView.dispatch_ will be updated to
    pass the new JWT key to JwtBuilder_, but only if

    * the requested token_type is *"jwt"* and
    * the access token is associated with a Restricted Application.

  * oauth_dispatch.validators_ will be updated to return *unexpired*
    JWT tokens for Restricted Applications, but ONLY if:

    * the token_type in the request equals *"jwt"* and
    * a `feature toggle (switch)`_ named "oauth2.enforce_jwt_scopes" is enabled.
      * **Note:** the toggle has since been retired with the equivalent of ``enforce_jwt_scopes`` value of True.

.. _edx-platform settings: https://github.com/openedx/edx-platform/blob/master/lms/envs/docs/README.rst
.. _JwtBuilder: https://github.com/openedx/edx-platform/blob/d3d64970c36f36a96d684571ec5b48ed645618d8/openedx/core/lib/token_utils.py#L15
.. _oauth_dispatch.views.AccessTokenView.dispatch: https://github.com/openedx/edx-platform/blob/d21a09828072504bc97a2e05883c1241e3a35da9/openedx/core/djangoapps/oauth_dispatch/views.py#L100
.. _oauth_dispatch.validators: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/dot_overrides/validators.py

4. Associate Available Scopes with Applications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to allow open edX operators to a priori limit the
types of access an Application can request, we will allow them
to configure Application-specific "available scopes".

* Introduce a new data model that associates available scopes with
  DOT Applications.

* Introduce a new Scopes Backend that extends DOT's SettingsScopes_
  backend and overrides the implementation of get_available_scopes_.

* The new backend will query the new data model to retrieve
  available scopes.

.. _get_available_scopes: https://github.com/evonove/django-oauth-toolkit/blob/2129f32f55cda950ef220c130dc7de55bea29caf/oauth2_provider/scopes.py#L17
.. _SettingsScopes: https://github.com/evonove/django-oauth-toolkit/blob/2129f32f55cda950ef220c130dc7de55bea29caf/oauth2_provider/scopes.py#L39

5. Associate Available Organizations with Applications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See 0007-include-organizations-in-tokens_ for decisions on this.

6. Introduce a new Permission class to enforce scopes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* New Permission class

  * The new `custom Permission`_ class will extend DOT's TokenHasScope_
    Permission class.

  * The TokenHasScope_ permission allows API endpoints to declare the
    scopes that they require in a *required_scopes* class variable.

* Enforcement by the Permission class

  * The permission class will verify that the scopes in the provided JWT
    are a proper superset of the *required_scopes* field set by the requested
    view.

  * For now, the permission class will skip this verification if the
    application is not a Restricted Application or if the token_type
    was not a JWT token.

    * **Note:** This will be an issue when microservices want to verify
      scopes. Determining whether an access token is associated with a
      Restricted Application is an LMS-specific capability. Given this,
      we may need to include a field in the token that indicates whether
      it was issued to a Restricted Application.

  * If the scopes verify, the permission class will update the request
    object with any organization values found in the token in an attribute
    called *allowed_organizations*. The view can then limit its access
    and resources by the allowed organizations.

* Using the Permission class

  * In order to have higher confidence that we don't inadvertently miss
    protecting any API endpoints, add the new Permission class to the
    `REST_FRAMEWORK's DEFAULT_PERMISSION_CLASSES`_ setting.

  * **Note:** Many of our API endpoints currently override this default
    by overriding the *permission_classes* field on their own View or ViewSet.
    So in addition to setting this default value, we will update all
    (15 or so) places that include JwtAuthentication_ in their
    *authentication_classes* field.

  * **Note:** We currently have both `function-based Django views`_ and
    class-based `Django Rest Framework (DRF)`_ views in the platform.

    * Authorization enforcement using Django Permission classes is
      supported only for DRF views. DRF does provide a `Python decorator`_
      to add DRF support to function-based views.

    * Only DRF enhanced views support JWT based authentication in our
      system. They do so via the DRF-based JwtAuthentication_ class.
      So we can **safely assume** that all JWT-supporting API endpoints
      can be protected via DRF's Permission class.

* Easy to disable

  * In case of an unexpected failure with this approach in production, use a
    `feature toggle (switch)`_ named "oauth2.enforce_token_scopes". When the
    switch is disabled, the new Permission class fails verification of all
    Restricted Application requests.

.. _custom Permission: http://www.django-rest-framework.org/api-guide/permissions/#custom-permissions
.. _TokenHasScope: https://github.com/evonove/django-oauth-toolkit/blob/50e4df7d97af90439d27a73c5923f2c06a4961f2/oauth2_provider/contrib/rest_framework/permissions.py#L13
.. _`REST_FRAMEWORK's DEFAULT_PERMISSION_CLASSES`: http://www.django-rest-framework.org/api-guide/permissions/#setting-the-permission-policy
.. _function-based Django views: https://docs.djangoproject.com/en/2.0/topics/http/views/
.. _Django Rest Framework (DRF): http://www.django-rest-framework.org/
.. _Python decorator: http://www.django-rest-framework.org/tutorial/2-requests-and-responses/#wrapping-api-views
.. _JwtAuthentication: https://github.com/openedx/edx-drf-extensions/blob/4569b9bf7e54a917d4acdd545b10c058c960dd1a/edx_rest_framework_extensions/auth/jwt/authentication.py#L17


Consequences
------------

* Putting these changes behind a feature toggle allows us to decouple
  release from deployment and disable these changes in the event of
  unexpected issues.

  * Minimizing the places that the feature toggle is checked (at the
    time of returning unexpired tokens and at the time of validating
    requests), minimizes the complexity of the code.

* By associating Scopes with DOT Applications and not Restricted
  Applications, we can eventually eliminate Restricted Applications
  altogether. Besides, they were introduced as a temporary concept
  until Scopes were fully rolled out.

* Microservices will continue to have limited scope support. We are
  consciously deciding to not address them at this time. When we do,
  we will also want to simplify and consolidate their OAuth-related
  logic and code.

.. _feature toggle (switch): https://openedx.atlassian.net/wiki/spaces/OpenDev/pages/40862688/Feature+Flags+and+Settings+on+edx-platform#FeatureFlagsandSettingsonedx-platform-Case1:Decouplingreleasefromdeployment
.. _0007-include-organizations-in-tokens: 0007-include-organizations-in-tokens.rst
