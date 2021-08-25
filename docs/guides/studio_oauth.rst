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

#. Configure Studio:

  - ``SOCIAL_AUTH_EDX_OAUTH2_KEY = '...client id...'``
  - ``SOCIAL_AUTH_EDX_OAUTH2_SECRET = '...client secret...'``
  - ``SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT = '...server-to-server LMS root URL...'``
  - ``SOCIAL_AUTH_EDX_OAUTH2_PUBLIC_URL_ROOT = '...public LMS root URL...``

#. Set ``LOGIN_URL`` for Studio to ``'/login/'`` and verify that it causes logins to use OAuth. Existing sessions should continue to work.


Cleanup
-------

Config and code changes to be performed after all environments are using OAuth flow for Studio.

- Set ``LOGIN_URL`` to ``'/login/'`` in ``cms/envs/common.py``
- Deploy
- Remove ``LOGIN_URL`` overrides from all environments (devstack and others)
- Remove remaining ``ARCH-1253`` detritus (login redirect)
- Remove this doc!
