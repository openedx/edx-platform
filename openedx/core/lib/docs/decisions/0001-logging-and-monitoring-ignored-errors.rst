Logging and monitoring ignored errors
=====================================

Status
------

Partially Superseded (see 0002-logging-and-monitoring-expected-errors-removed.rst)

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

The new feature adds the ability to mark errors as ignored, temporarily or permanently, even without "ignoring" them everywhere. For example, the errors and stacktraces would still appear, but it would be possible for alert conditions to ignore errors.

See how_tos/logging-and-monitoring-ignored-errors.rst for more information.

Changelog
---------

* **2023-09-28** - Changed status to "Partially Superseded", because expected errors will no longer be handled. See 0002-logging-and-monitoring-expected-errors-removed.rst for details.

* **2021-03-17** - Original "Accepted" ADR
