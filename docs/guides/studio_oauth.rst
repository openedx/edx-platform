Enabling OAuth for Studio login
===============================

Migration guide for edx.org (and anyone else following master) in converting Studio login to use OAuth.

This is a temporary document for Arch-BOM.

Background
----------

As of Lilac, the Studio by default shares a session cookie with the LMS.  This either forces Studio to be on a subdomain of the LMS or the LMS to set its session cookie on a wide domain, which exposes it to a potentially large number of subdomains.

By setting up Studio to use LMS's OAuth2-based single-sign-on (SSO), the cookies (and domains) can be decoupled to improve both flexibility and security.

Migration
---------

Most of the configuration is already in place, and Studio and LMS just need to be configured in each environment to enable the new flow. (Devstack and sandboxes will autoconfigure for OAuth.)

Migration involves simultaneously enabling OAuth and separating the session cookies for LMS and Studio. This effectively causes a logout for Studio users, although they'll still be logged into LMS and aside from a brief disruption during the mixed-config interval they should not experience many problems.

For each deployed environment (stage, production, etc.):

#. Register an SSO OAuth2 client in LMS:

   - Add OAuth2 client:

     - Go to ``/admin/oauth2_provider/application/add/`` in LMS admin
     - Copy the prepopulated client ID and secret to a secure place
     - Leave the user field empty
     - Set redirect URLs to ``<STUDIO_ROOT_URL>/complete/edx-oauth2/``
     - Set client type to ``Confidential``
     - Set authorization grant type to ``Authorization code``
     - Set the name to ``studio-sso``
     - Select the "Skip authorization" checkbox

   - Configure the client's scope:

     - Go to ``/admin/oauth_dispatch/applicationaccess/add/`` in LMS admin
     - Select application ``studio-sso``
     - Set scopes to ``user_id``

#. Configure LMS to log out Studio when logging out by adding ``<public Studio root>/logout/`` to the LMS ``IDA_LOGOUT_URI_LIST``.

#. Configure Studio to allow completion of OAuth flow::

    SOCIAL_AUTH_EDX_OAUTH2_KEY: <client id>
    SOCIAL_AUTH_EDX_OAUTH2_SECRET: <client secret>
    SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT: <server-to-server LMS root URL>  # possibly same as public LMS root URL
    SOCIAL_AUTH_EDX_OAUTH2_PUBLIC_URL_ROOT: <public LMS root URL>

#. Configure Studio to initiative OAuth flow and use a separate session cookie::

    LOGIN_URL: /login/  # to activate OAuth functionality
    SESSION_COOKIE_DOMAIN: <studio domain>  # since no longer using root domain to share with LMS
    SESSION_COOKIE_NAME: studio_sessionid

Cleanup
-------

Config and code changes to be performed after all environments are using OAuth flow for Studio.

- Set ``LOGIN_URL`` to ``'/login/'`` in ``cms/envs/common.py``
- Deploy
- Remove ``LOGIN_URL`` overrides from all environments (devstack and others)
- Remove remaining ``ARCH-1253`` detritus (login redirect)
- Remove this doc!
