Logging and monitoring ignored errors
=====================================

Status
------

Accepted

Context
-------

We had two recent Production issues that took longer than necessary to diagnose because they involved errors that are currently ignored by our Production monitoring configuration. One case took over 2 months to properly diagnose, and required temporary custom logging.

Decision
________

Add a capability for logging and monitoring ignored errors. The feature will be configurable, the monitoring will be available by default, and the logging will be opt-in as needed.

Note: This feature is being added to edx-platform to start, but could be moved to edx-django-utils monitoring for use in other IDAs.

Consequence
-----------

The new capabilities have been built in edx-platform, although they could be moved to edx-django-utils monitoring in the future for use in other IDAs.

The new feature adds the ability to mark errors as expected, temporarily or permanently, even without "ignoring" them everywhere. For example, the errors and stacktraces would still appear, but it would be possible for alert conditions to ignore expected errors.

For help configuring and using the new logging and monitoring features, see the `EXPECTED_ERRORS settings and toggles on Readthedocs`_.

.. _EXPECTED_ERRORS settings and toggles on Readthedocs: https://edx.readthedocs.io/projects/edx-platform-technical/en/latest/search.html?q=EXPECTED_ERRORS&check_keywords=yes&area=default
