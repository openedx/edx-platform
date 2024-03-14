15. Add scope user_id for JWT token
###################################

Status
------

Accepted

Context
-------

This ADR builds upon ADR 0015: Add Scope user_id for JWT Token. It inherits the context from that ADR, including the initial addition of the user_id claim for analytics and the rationale for using a scope to control its inclusion.

However, this ADR focuses specifically on the enterprise context highlighted in the consequences of ADR 0015. External organizations often utilize the LMS API with the grant_type: client_credentials to request tokens on behalf of their users. These tokens are crucial for enterprise integrations and require access to the user's user_id for proper functionality.

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

- Adding All Default Scopes: Including all scopes by default could potentially expose unnecessary user information. This approach prioritizes security over granular control.
- Default Inclusion with Opt-Out: This alternative explores automatically adding user_id for all cases and introducing an opt-out mechanism for specific scenarios where it's not required. Deferring this option allows for further analysis of potential security implications and user experience trade-offs.
