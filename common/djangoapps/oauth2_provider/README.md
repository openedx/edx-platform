edX OAuth2 Provider
===================
OAuth2 provider for edX Platform.


Instructions
------------

OAuth2 client must be registered to obtain their client_id and
client_secret. The registration can be done using the /admin web
interface, by adding new entries to the OAuth2 Clients table.

Apart from the two basic OAuth2 client types (public and
confidential), this provider as a notion of a trusted client. Such
clients to not require user approval for accessing user resources, and
will not show up the approval page during the sing-in process.

To make a client trusted after it has been created, add it to the
OAuth2-provider TrustedModel tables using the /admin web interface.
