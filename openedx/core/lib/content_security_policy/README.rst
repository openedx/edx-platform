Content-Security-Policy Middleware
**************************

.. The preferred way to prevent clickjacking is to use the Content Security Policy headers.
.. This middleware adds the Content-Security-Policy headers to the response.
.. It allows overriding the default Content-Security-Policy header for specific urls by
.. setting the CUSTOM_CSPS environment variable.

- Add the middleware ``'openedx.core.lib.content_security_policy.middleware.content_security_policy_middleware',`` near the beginning of your ``MIDDLEWARE`` list.
