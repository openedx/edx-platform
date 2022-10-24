7. Include Organizations in Tokens
----------------------------------

Status
------

Accepted

Context
-------

Status of Organizational Access to edX APIs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

External edX applications would like to make server-to-server API
calls via the Client Credentials grant type to access data. However,
our APIs typically return data only to global staff users who
effectively have administrative read access to the system. This
all-or-nothing capability is unsatisfactory to meet the needs of
edX partner organizations.

Additionally, some organizations create their own web portals for
their learners, using edX as an identity provider and as the underlying
LMS. For various reasons (?), they would like to present edX data to
their learners on their own portal. Currently, they cannot access a
learner's data using our APIs.

Our API endpoints do not have more flexible capabilities since they
do not have reliably sufficient information to limit/filter API results
according to the organizational affiliation of the requesting application.

Organizational Types in the edX System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here are a few organizational relationships that exist in the edX system:

* **Organization as a Content Provider**

  * This is a partner organization that provides content for a course,
    program, etc. Typically, such an organization will want to access
    data for all learners enrolled in their courses. They may choose to
    do so either via

    a. bulk APIs using the *Client Credentials grant type* (e.g., to
       synchronize their own data in a background process) or

    b. a user-specific API on behalf of a logged-in user via the
       *Authorization grant type* and *edX as the identity provider*
       (e.g., to display user-specific data on their own portal).

* **Organization as a User Provider**

  * This is an enterprise organization that registers users onto the
    edX system, typically via an SSO-enabled portal, but with the
    *organization (not edX) as the identity provider*. Such an
    organization will also want to access data for all its users.

* **Organization as a Credit Provider**

  * This is an institution or employer that recognizes edX credentials for
    a course, program, etc. A user would selectively grant organizations
    permissions to access her edX records and information.

Decisions
---------

In order to allow DOT Applications to access data for their own organization
without inadvertently or maliciously gaining access to data for other
organizations, (1) applications need to be linked to their own organizations,
(2) organization information needs to be cryptographically bound with
issued tokens and the (3) the authorization approval form needs to present the
organization information to the granting end-user.

1. Associate Available Organizations with DOT Applications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Create a configurable Application-specific "available organizations"
  setting, which is akin to Application-specific "available scopes"
  (as described in 0006-enforce-scopes-in-LMS-APIs_).

* Introduce a new data model that associates available organizations
  with DOT Applications.

* The new data model will have a Foreign Key to the Organization_ table.
  It will essentially be a many-to-many relationship between Organizations
  and DOT Applications.

* The new data model will also have a column for specifying organization
  type: *content_provider*, *user_provider*, *credit_provider*, etc.
  Initially, we will only use *content_provider*.

2. Organization and Users as Filters in OAuth Tokens
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The organization associated with the Application will be specified
  in a new *filters* field in the JSON Web Token (JWT).

* The value of the *filters* field will include what *type* of organization
  it is (per`Organizational Types in the edX System`_).  For example:

    "content_org:Microsoft"

* For a token created on behalf of a user (*not* created via a
  *Client Credentials grant type*), the token
  is further restricted specifically for the granting user.  And so, a
  "user" filter with the value "me" would be added for this grant type.
  For example:

    "user:me"

* JwtBuilder_'s *build_token* functionality will be extended to include
  the filters in the token's payload. This payload is
  cryptographically signed and so binds and limits the scopes in the
  token to the filters.

* Since filters are inside the token, any relying party
  that receives the token (any microservice) will be able to
  enforce scopes as limited by the filters. API endpoints will limit the
  values returned in their payloads by the specified filters.

.. _0006-enforce-scopes-in-LMS-APIs: 0006-enforce-scopes-in-LMS-APIs.rst
.. _Organization: https://github.com/openedx/edx-organizations/blob/fa137881be9b7d330062bc32655a00c68635cfed/organizations/models.py#L14
.. _JwtBuilder: https://github.com/openedx/edx-platform/blob/d3d64970c36f36a96d684571ec5b48ed645618d8/openedx/core/lib/token_utils.py#L15

3. Organization Information in Authorization Approval Form
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the interstitial authorization approval form is presented to the
user for granting access to a DOT Application, if the Application is
associated with an Organization, the Organization value(s) should be
presented to the user. This makes it clear to the user that the
granted access is limited to the Organization's affiliations.

Token Examples
--------------

Client Credentials (server-to-server) grant type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a trusted application makes server-to-server calls, the application's
service user info is included in the JWT and the *filters* field
includes the organization identifier and type associated with the application.

::

  {
    "scopes": ["grades:read", "enrollments:read"],
    "filters":  ["content_org:Microsoft"],
    "version": "1.0",
    "preferred_username": "microsoft_service_user",
    ...
  }

Authorization Code and Password-based (on behalf of user) grant types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a user-approved application or a trusted mobile app makes calls on behalf
of the approving user, the user's info is included in the token along with a
filter “me” in the *filters* field.

::

  {
    "scopes": ["grades:read", "enrollments:read"],
    "filters":  ["content_org:Microsoft", "user:me"],
    "version": "1.0",
    "preferred_username": "ajay_mehta",
    ...
  }

Consequences
------------

* By associating organizations with DOT Applications and not Restricted
  Applications, we can eventually eliminate Restricted Applications
  altogether.

* By including the organization value and its type in the token, any relying party
  that receives the token (including a microservice) will be able to
  enforce the scopes as limited to the organization.

* Having a separate field for *filters* introduces a clear boundary for
  separation of concerns of what is enforced at each layer:

  * **API endpoint** declares the *required scopes*.
  * The base **Django Permission** class enforces *required scopes*.
  * **API gateway** (in the future) may additionally enforce *required scopes*.
  * **API endpoint** enforces the *required filters*.

* When a new filter type is introduced in the future, we will have to
  make sure there are no security issues introduced where old endpoints
  that are not aware of the new filter do not enforce it.  Possible
  ways of doing so are:

  * Endpoints that are highly security sensitive should reject any
    token that includes an unrecognized filter.

  * Multi-phase rollout with a major version update of tokens once all
    microservices and relevant endpoints have updated to recognize the new
    filter. Tokens with the new filter would be issued only after all relevant
    endpoints have been updated.

* Alternatively, we could have embedded the filter-type within the *scopes*
  field of the token. This would support a more secure path forward since
  old endpoints would automatically reject new filter-types in scopes that
  they don't recognize. For example:

    "grades:read:content_org"

  Additionally, this alternative would allow tokens to specify different filters
  for different scopes.

  However, this alternative was rejected since it added unnecessary confusion
  in understanding and parsing scope values. Additionally keeping filters
  independent allows them to evolve and grow (more complex) over time without
  trying to coerce their values within scope expressions.

References
----------

* Examples of Scopes in other web systems

  * https://developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps/
  * https://developers.google.com/identity/protocols/googlescopes
  * https://api.slack.com/scopes
  * https://developer.spotify.com/web-api/using-scopes/
  * https://developer.atlassian.com/server/hipchat/hipchat-rest-api-scopes/
