Logging and monitoring of expected errors removed
=================================================

Status
------

Accepted

Context
-------

The setting ``EXPECTED_ERRORS`` was used for both expected and ignored errors in edx-platform.

The functionality supporting expected errors was added:

* Because New Relic didn't yet support this for Python, and
* Because it was thought that people may want more flexibility for marking errors as expected in addition to just the class name, and
* The setting provides a place to document why the change is being made.

Updates regarding these three original reasons:

* New Relic now supports expected errors, so the custom functionality is redundant and complicated, and
* This functionality has yet to be used, so it is also unnecessary.

Note that the need for custom functionality for ignored errors differs from expected errors in the following ways:

* New Relic still has problems from time to time where it stops ignoring errors that it is supposed to be ignoring, and this redundant functionality is used to catch that issue, and
* Since New Relic does not capture details of ignored errors, the custom functionality to log these errors can still come in handy if more details are needed.

This context can also be found in `[DEPR] Expected error part of EXPECTED_ERRORS`_.

.. _[DEPR] Expected error part of EXPECTED_ERRORS: https://github.com/openedx/edx-platform/issues/32405

Decision
________

The custom ignored error functionality proposed in 0001-logging-and-monitoring-ignored-errors.rst will remain in place, but the custom expected error functionality will be removed.

Consequence
-----------

* A number of code changes are required to remove the expected functionality.

  * In many placed in the code, "expected" was used to mean "ignored and expected", and all such instances will be renamed to "ignored".
  * The setting ``EXPECTED_ERRORS`` will be renamed to ``IGNORED_ERRORS``, which better matches how it was being used in the first place.
  * The setting ``EXPECTED_ERRORS[REASON_EXPECTED]`` will be renamed to ``IGNORED_ERRORS[REASON_IGNORED]``.
  * The setting toggle ``EXPECTED_ERRORS[IS_IGNORED]`` will be removed, because it will now always be True.
  * The how-to will be renamed to how_tos/logging-and-monitoring-ignored-errors.rst.
  * For more details, see https://github.com/openedx/edx-platform/pull/33184 where this work is underway.

* If anyone ever uses New Relic's expected error functionality, the reason for marking an error as expected would need to be captured elsewhere.
