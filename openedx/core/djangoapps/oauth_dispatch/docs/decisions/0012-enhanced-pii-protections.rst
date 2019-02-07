12. Enhanced PII Protection
===========================

Status
------

Draft

Context
-------

The `original implementation of the JWT payload`_ contains some PII (Personally Identifiable Information) related issues we would like to improve:

* The JWT includes some PII, like the username, by default.

* The OAuth2 *profile* scope packages both PII and non-PII fields together, even though the *administrator* field could be useful on its own.

* The *sub* field should be the unique identifier of the subject, in this case, the user id. However, the *sub* does not currently contain the *LMS user_id* as the unique user identifier, as described in the (draft) proposal `oep-0032-arch-unique-identifier-for-users`_.

For more background, please see:

* `Use JWT as OAuth2 Tokens`_, where we decided to use JWTs for our oAuth2 tokens.

* More information on PII (Personally Identifiable Information) in `oep-0030-arch-pii-markup-and-auditing`_

.. _original implementation of the JWT payload: https://github.com/edx/edx-platform/blob/9a0812fcdea5e023637b8b2030abd7ae5de5b07d/openedx/core/djangoapps/oauth_dispatch/jwt.py#L106-L119
.. _0006-enforce-scopes-in-LMS-APIs: 0006-enforce-scopes-in-LMS-APIs.rst
.. _oep-0032-arch-unique-identifier-for-users: https://github.com/edx/open-edx-proposals/pull/103
.. _Use JWT as OAuth2 Tokens: 0003-use-jwt-as-oauth-tokens-remove-openid-connect.rst
.. _oep-0030-arch-pii-markup-and-auditing: https://open-edx-proposals.readthedocs.io/en/latest/oep-0030-arch-pii-markup-and-auditing.html

Decisions
---------

The following general guidelines should be following when defining PII related JWT payload fields:

* PII fields should never be included by default, and should require an oAuth scope.

* OAuth2 scopes should not package both PII and non-PII fields using a single scope, unless the non-PII fields are meaningless without the PII fields. This enables someone to be authorized for non-PII fields without forcing additional PII authorization.

In order to correct these and other PII related issues with the current JWT payload, the following updates will be introduced:

* Access to the username (which is considered PII) will now be protected by an OAuth scope, rather than being returned by default.

* The *administrator* field will be made accessible outside of the *profile* scope. The details of the new field and/or scope are TBD.

* The *sub* field will now contain the *LMS user_id*.

  * It is unclear whether the previous value of ``anonymous_id_for_user()`` will be needed in a new field for backward compatibility. It will be left out for now, since it can easily be added later without introducing a breaking change.

In order to enable the breaking changes above, a new major version will be introduced.

Rejected Alternatives
---------------------

Fixing Without Breaking Changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Removing the username from the default fields cannot be done without it being a breaking change.

Additionally, given the timing of these changes and current limited usage of OAuth scopes thus far, it is an opportune time to get the advantages of increased clarity that come from making breaking changes.  For example, had we decided to leave *sub* as-is and introduce another field named *user_id*, it would be more difficult for engineers to know what to use when, and why *sub* isn't the main id we want people to use.
