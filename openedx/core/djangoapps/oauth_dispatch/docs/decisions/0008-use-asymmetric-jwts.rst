8. Use Asymmetric JWTs
----------------------

Status
------

Accepted

Context
-------

The edX OAuth Provider (via this OAuth Dispatch Django app) builds and returns JSON Web Tokens (JWTs)
when an OAuth client requests an access token with "token_type=jwt" in the request. See `Use JWT as
OAuth2 Tokens; Remove OpenID Connect`_.

We use a shared secret ("symmetric" cryptographic key) to "sign" the JWT with an HMAC (a keyed-hash
message authentication code). This means the secret used by the OAuth Provider to create JWTs is not
really a secret since all OAuth Clients need to know the value of the secret in order to verify the
contents of the JWT.

The JWT is currently not encrypted, only signed. So any client can always read the contents of the JWT.
But to verify that the JWT was created by the OAuth Provider, the client should first verify the HMAC
sent along with the JWT. Since the secret is "symmetric" any OAuth Client that is privy to the secret
could also have just as easily created the JWT (thus spoofing the OAuth Provider).

.. _`Use JWT as OAuth2 Tokens; Remove OpenID Connect`: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/oauth_dispatch/docs/decisions/0003-use-jwt-as-oauth-tokens-remove-openid-connect.rst

Additionally, for clients that still use Open ID Connect, their `ID Tokens are HMACed with their own
client_secret`_ (privately shared with the OAuth Provider). Although this somewhat mitigates the issue
above since each OAuth Client can no longer create tokens verifiable by other Clients, it does not
allow a Client to forward a verifiable token to other Clients.

.. _ID Tokens are HMACed with their own client_secret: https://github.com/edx/edx-oauth2-provider/blob/7e59e30ae0bfd9eac4d05469768d79c50a90aeb7/edx_oauth2_provider/views.py#L155-L163

Looking forward, we want to support Single Page Apps (a.k.a., Microfronteds), where users can seamlessly
traverse from one microfronted to another and access APIs on various backends. This *Single Sign On*
capability cannot be achieved unless verifiable tokens can be forwarded from one service to another.

Decisions
---------

Asymmetric JWTs
~~~~~~~~~~~~~~~

We will introduce identified "asymmetric" cryptographic keys for signing JWTs. The OAuth Provider will
be the only service configured with the aymmetric keypair, including its Private and Public key portions.
All other OAuth Clients will be configured with only the Public key portion of the asymmetric key pair.
This will ultimately replace all uses of "symmetric" keys for signing JWTs.

"kid" Key Identifier
~~~~~~~~~~~~~~~~~~~~

In order to support key rotation in a forward compatible manner, we will identify the asymmetric keys,
using the `JSON Web Key (JWK)`_ standard's `"kid" (Key ID)`_ parameter.  When a `JSON Web Signature (JWS)`_
is created to sign a JWT, its `"kid" header parameter`_ specifies which key was used to secure the JWS.
The code examples below show this in action.

.. _JSON Web Key (JWK): https://tools.ietf.org/html/draft-ietf-jose-json-web-key-36
.. _`"kid" (Key ID)`: https://tools.ietf.org/html/draft-ietf-jose-json-web-key-36#section-4.5
.. _JSON Web Signature (JWS): https://tools.ietf.org/html/rfc7515
.. _`"kid" header parameter`: https://tools.ietf.org/html/rfc7515#section-4.1.4

Remove JWT_ISSUERS
~~~~~~~~~~~~~~~~~~

`edx_rest_framework_extensions.settings`_ supports having a list of **JWT_ISSUERS** instead of just a single
one. This support for configuring multiple issuers is present across many services. However, this does not
conform to the `JWT standard`_, where the `issuer`_ is intended to identify the entity that generates and
signs the JWT. In our case, that should be the single Auth service only.

If different values for the issuer_ claim are needed for multi-tenancy purposes, those should be specified
using `site configuration`_ variants instead of adding complexity with multiple issuers.

Additionally, **JWT_ISSUERS** is not intended to be used for key rotation. Rather, the set of active signing
keys should be specified as a `JSON Web Key Set (JWK Set)`_ instead. Thus, there would only be a single
issuer, but with (the potential of) multiple signing keys stored in a JWT Set.

.. _edx_rest_framework_extensions.settings: https://github.com/openedx/edx-drf-extensions/blob/1db9f5e3e5130a1e0f43af2035489b3ed916d245/edx_rest_framework_extensions/settings.py#L73
.. _JWT standard: https://tools.ietf.org/html/rfc7519
.. _issuer: https://tools.ietf.org/html/rfc7519#section-4.1.1
.. _JSON Web Key Set (JWK Set): https://tools.ietf.org/html/draft-ietf-jose-json-web-key-36#section-5
.. _site configuration: https://github.com/openedx/edx-platform/blob/af841336c7e39d634c238cd8a11c5a3a661aa9e2/openedx/core/djangoapps/site_configuration/__init__.py

Features
--------

KeyPair Generation
~~~~~~~~~~~~~~~~~~

Please have a look at ``openedx/core/djangoapps/oauth_dispatch/management/commands/generate_jwt_signing_key.py``
to get better understanding how to generate keypair using ``PyJWT``.

The public and private keypair would be similar to the following::

    ## Public keyset
    """
        {
            "keys": [
                {
                    "kty": "RSA",
                    "key_ops": ["verify"],
                    "n": "...",
                    "e": "...",
                    "kid": "your_key_id"
                }
            ]
        }
    """


    ## Private key
    """
        {
            "kty": "RSA",
            "key_ops": ["sign"],
            "n": "...",
            "e": "...",
            "d": "...",
            "p": "...",
            "q": "...",
            "dp": "...",
            "dq": "...",
            "qi": "...",
            "kid": "your_key_id"
        }
    """

Signing
~~~~~~~

To create a signature you simply need a **payload**, **private key** and your hashing algorithm::

    signed_message = jwt.encode("JWT payload in dict format", key=private_key, algorithm="RS512")

Note: we specify **RS512** above to identify *RSASSA-PKCS1-v1_5 using SHA-512* as
the signature algorithm value as described in the `JSON Web Algorithms (JWA)`_ spec.

.. _JSON Web Algorithms (JWA): https://tools.ietf.org/html/rfc7518#section-3.3

Verify Signature
~~~~~~~~~~~~~~~~

To verify the signature we'll be looping through the public keys and try to verify the signature with each of them.
For more details you can have a look at `verify_jwk_signature_using_keyset`_. To generate ``keyset`` required for verification you
can use `get_verification_jwk_key_set`_ method.

.. _verify_jwk_signature_using_keyset: https://github.com/openedx/edx-drf-extensions/blob/master/edx_rest_framework_extensions/auth/jwt/decoder.py#L270
.. _get_verification_jwk_key_set : https://github.com/openedx/edx-drf-extensions/blob/master/edx_rest_framework_extensions/auth/jwt/decoder.py#L395

Key Rotation
~~~~~~~~~~~~

In future if we plan to rotate the keys, we can simply add new key public key to the public keyset and remove the old private one.
Means, at any time there might be more than one public key but there will be only one private key. Considering that we are doing verification
by looping through all the available public keys, the ``kid`` parameter is not
as important as it was before. But it's still recommended to use it. It will help us to differentiate between the old and new public keys.

Consequences
------------

* As described in the Context_, there are both security and feature (Single Sign On)
  benefits of using asymmetric JWTs.

* As we transition away from DOP and Open ID Connect (see past decisions), we continue
  to have multiple authentication implementations in the platform. Introducing
  asymmetric JWTs introduces yet another. The sooner we upgrade our dependent services
  and remove these other mechanisms, the better - in the meantime, we are increasing
  code complexity.

* All uses of "symmetric" keys used for signing JWTs should be marked as deprecated
  until they can be removed. Pointing to this decision record from other code will
  quickly explain and help identify outstanding work for removal.
