Content-Security-Policy Middleware
**********************************

.. The preferred way to prevent clickjacking is to use the Content Security Policy headers.
.. This middleware adds the Content-Security-Policy headers to the response.
.. It allows overriding the default Content-Security-Policy header for specific urls.

- Add the middleware ``'openedx.core.lib.content_security_policy.middleware.content_security_policy_middleware',``
  near the beginning of your ``MIDDLEWARE`` list.
- To add a Content-Security-Policy header for all endpoints, set the ``CSP_STATIC_ENFORCE`` setting to
  the desired value for the header; this excludes only the reporting options.
- If desired, the ``CSP_STATIC_REPORT_ONLY``, ``CSP_STATIC_REPORTING_URI``, and ``CSP_STATIC_REPORTING_NAME``
  settings can be added to enable reporting of violations.
- If you want different CSP headers for specific URLs, define a function
  like in the example ``_get_custom_csps`` below and then assign this function
  to the ``GET_CUSTOM_CSPS`` setting.
- This defines a callback function that will be executed by the middleware.
  The function should return a list of value pairs like ``[['.*/example-regex', 'example-csp-header-string']]``,
  where each pair contains a regex pattern
  and a CSP header value to be applied to URLs that match the pattern.
- If no ``CSP_STATIC_ENFORCE`` setting is defined, the middleware will only add the header for the URLs matching
  the patterns specified in the ``GET_CUSTOM_CSPS`` function return.
- If the ``CSP_STATIC_ENFORCE`` setting is defined as well, the custom CSP headers will take precedence
  for the specified URLs.
- The reason a callback function is used is that django configuration settings like ``LEARNING_MICROFRONTEND_URL``
  are not available at the time the settings are loaded, so the function is called at runtime.

Example for ``_get_custom_csps`` callback function:
---------------------------------------------------

```
def _get_custom_csps():
  from django.conf import settings
  learning_url = getattr(settings, 'LEARNING_MICROFRONTEND_URL', None)
  return [
      ['.*/media/scorm/.*', f"frame-ancestors 'self' {learning_url}"],
      ['.*/xblock/.*', f"frame-ancestors 'self' {learning_url}"]
  ]
```
