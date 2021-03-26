How to log and monitor expected errors
======================================

What are expected and ignored errors?
-------------------------------------

Errors might be "expected" for various reasons. Some examples:

* Errors like ``PermissionDenied``, or ``Ratelimited``, where users or bots are prevented from doing something that is not allowed.
* Errors that we have already diagnosed, but may either not be worth fixing, or we are unable to fix for some time.

In some cases, a bug could introduce a large number errors where an "expected" error becomes an "unexpected" error. Or, there might be certain request paths for which the same error may be expected or unexpected.

A subset of "expected" errors are "ignored" errors. edX uses New Relic, which can be configured to ignore errors. These errors get suppressed and leave no (stack) trace, and won't trigger error alerts.

Monitoring expected errors
--------------------------

At a minimum, it is recommended that you add monitoring for any expected errors, including ignored errors. You do this by using the ``EXPECTED_ERRORS`` setting. For details on configuring, see the documentation for `EXPECTED_ERRORS settings and toggles on Readthedocs`_.

This will provide an ``error_expected`` custom attribute for every expected error. This custom attribute can be used in the following ways.

* Use ``WHERE error_expected IS NULL`` to filter out expected errors from most alert conditions.
* Set up special alerts for an overabundance of expected errors using ``WHERE error_expected IS NOT NULL``.

Additionally, a subset of expected errors that are configured as ignored will also get ``error_ignored_class`` and ``error_ignored_message`` custom attributes.

* Using New Relic terminology, this extra error class and message data will live on the Transaction and not the TransactionError, because ignored errors won't have a TransactionError.
* Use these additional custom attributes to help diagnose unexpected issues with ignored errors.

.. _EXPECTED_ERRORS settings and toggles on Readthedocs: https://edx.readthedocs.io/projects/edx-platform-technical/en/latest/search.html?q=EXPECTED_ERRORS&check_keywords=yes&area=default

Logging expected errors
-----------------------

Following the same documentation as for monitoring, you can also enable logging with or without a stack trace. This additional information may be useful for tracking down the source of a mysterious appearance of an otherwise expected error.

More targeted scoping of errors
-------------------------------

The initial implementation only enables this functionality by error ``module.Class``. If you need to scope the monitoring/logging for a more limited subset, like for certain requests, the expectation would be to enhance and document these new capabilities.
