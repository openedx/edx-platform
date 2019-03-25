2. Migrate to Django OAuth Toolkit
----------------------------------

Status
------

Accepted

Context
-------

The edX LMS uses the `Django OAuth Provider (DOP)`_ library in order to support
the OAuth2_ provider protocol. However, that library is now unsupported and
deprecated by the Django community. Additionally, the edX mobile apps, which are
OAuth2 clients of the LMS, need the capability to refresh tokens, which DOP does
not support for `Public Client`_ types that use `Password Credentials grant`_.

.. _OAuth2: https://tools.ietf.org/html/rfc6749
.. _Public Client: https://tools.ietf.org/html/rfc6749#section-2.1
.. _Password Credentials grant: https://tools.ietf.org/html/rfc6749#section-4.3
.. _Django OAuth Provider (DOP): https://github.com/caffeinehit/django-oauth2-provider

Decision
--------

Moving forward, we will use the `Django OAuth Toolkit (DOT)`_ library and remove
our use of DOP. 

.. _Django OAuth Toolkit (DOT): https://github.com/evonove/django-oauth-toolkit

Consequences
------------

Pluses
~~~~~~

* The `Django documentation recommends DOT`_ for OAuth 2.0 support, so there
  should be ample support for it in the community.

* DOT uses the well maintained and recommended OAuthLib_ library for the basic
  OAuth flow so it has a solid crypto foundation.

* DOT is extensible, including its various polymorphic classes and configurable
  settings.

* DOT seems to have the basic OAuth2 features that we will need for the
  foreseeable future, including refresh tokens and scopes.

.. _Django documentation recommends DOT: http://www.django-rest-framework.org/api-guide/authentication/#django-oauth-toolkit
.. _OAuthLib: https://github.com/idan/oauthlib

Minuses
~~~~~~~

* We need to remove all usages of DOP before we can remove the library.
