Enabling OAuth for Studio login
###############################

This is a migration guide for converting Studio login to use OAuth, for use in the Lilac to Maple upgrade.

Background
**********

As of Lilac, the Studio by default shares a session cookie with the LMS.  This either forces Studio to be on a subdomain of the LMS or the LMS to set its session cookie on a wide domain, which exposes it to a potentially large number of subdomains.

Maple's configuration assumes that Studio will use LMS's OAuth2-based single-sign-on (SSO). This means that the cookies (and domains) can be decoupled to improve both flexibility and security. However, there are a few steps to take to finish this configuration (otherwise Studio logins will not work.)

Migration
*********

Studio and LMS need to be configured in each environment to enable the new flow, with the exception of devstack and sandboxes (which will autoconfigure for OAuth.) Migration involves enabling OAuth and separating the session cookies for LMS and Studio. The session cookie split will require Studio users to log in again.

Follow these steps for each deployed environment (stage, production, etc.):

#. Create a ``studio_worker`` service account in the LMS::

    ./manage.py lms manage_user studio_worker some-email@your-domain --unusable-password

#. Register an SSO OAuth2 client in LMS::

    ./manage.py lms create_dot_application --grant-type authorization-code --skip-authorization --redirect-uris "https://studio.YOURSITE/complete/edx-oauth2/" --scopes "user_id" studio-sso studio_worker

#. Configure LMS to log out Studio when logging out by adding ``<public Studio root>/logout/`` to the LMS ``IDA_LOGOUT_URI_LIST``.

#. Find your new client in your LMS Django admin (``/admin/oauth2_provider/application/?q=studio-sso``) and then configure Studio to allow completion of OAuth flow::

    SOCIAL_AUTH_EDX_OAUTH2_KEY: <client id>
    SOCIAL_AUTH_EDX_OAUTH2_SECRET: <client secret>
    SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT: <server-to-server LMS root URL>  # possibly same as public LMS root URL
    SOCIAL_AUTH_EDX_OAUTH2_PUBLIC_URL_ROOT: <public LMS root URL>

#. Configure Studio to initiate OAuth flow and use a separate session cookie::

    SESSION_COOKIE_NAME: studio_sessionid

This cookie renaming step is also a good opportunity to change ``SESSION_COOKIE_DOMAIN`` if desired, since it allows for a clean transition without having to worry about `flaky behavior driven by order-unstable cookie-sending <https://fwielstra.github.io/2017/03/13/fun-with-cookies-and-subdomains/>`_. Narrowing the domain (or removing it, to keep subdomains from seeing the cookie) may improve the security of your deployment, but the best option depends on the exact layout of your domain names and is beyond the scope of this document.
