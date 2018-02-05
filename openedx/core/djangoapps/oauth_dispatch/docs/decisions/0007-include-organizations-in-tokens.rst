7. Include Organizations in Tokens
----------------------------------

Status
------

Proposed

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

In the edX system, the 2 most prevalent organizational relationships
are:

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
    However, it is not an immediate requirement to support data
    access by this organization type at this time.

Decisions
---------

In order to allow DOT Applications to access data for their own organization
without inadvertently or maliciously gaining access to data for other
organizations, (1) applications need to be linked to their own organizations,
(2) organization information needs to be cryptographically bound with
issued tokens, (3) the authorization approval form needs to present the
organization information and (4) organization limitations need to be
embedded in the scopes.

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
  type: *content_provider* or *user_provider*. Initially, we will only
  use *content_provider*.

2. Organization Information in OAuth Tokens
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The organization associated with the Application will be included
  in the JWT tokens requested by the Application.

* JwtBuilder_'s *build_token* functionality will be extended to include
  the organization value in the token's payload. This payload is
  cryptographically signed and so binds and limits the scopes in the
  token to the organization.

* Since the organization value is inside the token, any relying party
  that receives the token (including a microservice) will be able to
  enforce scopes as limited to the organization.

.. _0006-enforce-scopes-in-LMS-APIs: 0006-enforce-scopes-in-LMS-APIs.rst
.. _Organization: https://github.com/edx/edx-organizations/blob/fa137881be9b7d330062bc32655a00c68635cfed/organizations/models.py#L14
.. _JwtBuilder: https://github.com/edx/edx-platform/blob/d3d64970c36f36a96d684571ec5b48ed645618d8/openedx/core/lib/token_utils.py#L15

3. Organization Information in Authorization Approval Form
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the interstitial authorization approval form is presented to the
user for granting access to a DOT Application, if the Application is
associated with an Organization, the Organization value(s) should be
presented to the user. This makes it clear to the user that the
granted access is limited to the Organization's affiliations.

4. Embed Organization Limitation Types in Scopes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Since individual API endpoints need to enforce both scopes and their
  corresponding organization limitations as included in the token, the
  scopes themselves should indicate whether or not organization limitations
  apply.

* In the event that we add additional types of organization limits in
  the token, we would introduce new scopes that enforce the new
  types of limits.

  * This allows us to introduce new types of limits while being assured
    that pre-existing API endpoints will remain protected. Since the
    pre-existing endpoint is unaware of the new scope, it will
    prevent access until it is updated to support the new type of 
    organization limit.

Scopes Examples
---------------

Here is an initial list of scopes that we may support. Notice how some
enforce organization limits and others don't. When configuring a DOT
Application, the edX operator decides how much access the application
is permitted.

+-------------------------------+----------------------------------------------------------------+ 
| Scope                         | Allowed access                                                 |
+===============================+================================================================+
| certificates:read             | Retrieve any certificate                                       |
+-------------------------------+----------------------------------------------------------------+ 
| certificates:read:content_org | Retrieve certificates for courses provided by the organization |
+-------------------------------+----------------------------------------------------------------+ 
| grades:read                   | Retrieve any grade                                             |
+-------------------------------+----------------------------------------------------------------+ 
| grades:read:content_org       | Retrieve grades for courses provided by the organization       |
+-------------------------------+----------------------------------------------------------------+ 
| enrollments:read              | Retrieve any enrollment information                            |
+-------------------------------+----------------------------------------------------------------+ 
| enrollments:read:content_org  | Retrieve enrollments for courses provided by the organization  |
+-------------------------------+----------------------------------------------------------------+ 

**Note:** Each of these scopes can be used in a server-to-server
API call (via Client Credentials) or an API call on behalf of a
single user (via Authorization Code).

Consequences
------------

* By associating organizations with DOT Applications and not Restricted
  Applications, we can eventually eliminate Restricted Applications
  altogether.

* By including the organization value in the token, any relying party
  that receives the token (including a microservice) will be able to
  enforce the scopes as limited to the organization.

* Including the organization limitation types in the scope allows for
  a secure path forward to introduce new types of limitations in the
  future. It also makes it clearer to API endpoints what needs to be
  enforced.

References
----------

* Examples of Scopes in other web systems

  * https://developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps/
  * https://developers.google.com/identity/protocols/googlescopes
  * https://api.slack.com/scopes
  * https://developer.spotify.com/web-api/using-scopes/
  * https://developer.atlassian.com/server/hipchat/hipchat-rest-api-scopes/
