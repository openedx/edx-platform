16. Add scope user_id for JWT token and client credentials grant type
#####################################################################

Status
------

Accepted

Context
-------

This ADR builds upon ADR 0015: Add Scope user_id for JWT Token. It inherits the context from that ADR, including the initial addition of the user_id claim for analytics and the rationale for using a scope to control its inclusion.

However, this ADR focuses specifically on the enterprise context highlighted in the consequences of ADR 0015. External organizations often utilize the LMS API with the grant_type: client_credentials to request tokens on behalf of their users. These tokens are crucial for enterprise integrations and require access to the user's user_id for proper functionality.

Based on 0005-restricted-application-for-SSO_ and 0006-enforce-scopes-in-LMS-APIs_ ADRs, it may be that the original purpose of the user_id scope was to protect against leakage of the user_id in the case of some combination of Authorization Grant and Restricted Applications. More investigation would be required to refactor based on this context, but it may be useful for future iterations.

.. _0005-restricted-application-for-SSO: 0005-restricted-application-for-SSO.rst
.. _0006-enforce-scopes-in-LMS-APIs: 0006-enforce-scopes-in-LMS-APIs.rst

The current implementation requires clients to remember to request using the scope, which is not a trustworthy solution.

Decisions
---------

- The scope ``user_id`` will be added to all requests having grant_type ``client_credentials`` in the API `/oauth2/access_token/`, if it is an allowed scope in the DOT Application and the payload request does not have `scopes` attribute in it.

Consequences
------------

- Enterprises will have the flexibility to request the user_id claim in JWT tokens issued through the client_credentials grant. This enables them to integrate seamlessly with LMS functionalities requiring user identification.
- The existing behavior for other grant types (like password) defined in ADR 0015 remains unchanged.
- This pattern will be used to clean-up the manually added ``user_id`` scope for oauth clients using the enterprise public APIs.

Deferred/Rejected Alternatives
------------------------------

- Adding all allowable scopes as default: Including all allowable scopes by default, which would include the user_id scope, would not follow the principle of least privilege and would make every default token have more access than required. Instead, we will minimize the additional access.
- Default Inclusion with Opt-Out: This alternative explores automatically adding user_id for all cases and introducing an opt-out mechanism for specific scenarios where it's not required. Deferring this option allows for further analysis of potential security implications and user experience trade-offs.
- See the context section for additional thoughts around Authorization Grant type and Restricted Applications.