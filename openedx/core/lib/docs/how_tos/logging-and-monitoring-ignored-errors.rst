How to log and monitor ignored errors
======================================

What are ignored errors?
-------------------------------------

Operators of Open edX might use New Relic for monitoring, which can be configured to ignore errors. These errors get suppressed and leave no (stack) trace, and won't trigger error alerts.

Monitoring ignored errors
--------------------------

At a minimum, it is recommended that you add monitoring for any ignored errors. You do this by using the ``IGNORED_ERRORS`` setting. For details on configuring, see the documentation for `IGNORED_ERRORS settings and toggles on Readthedocs`_.

This will provide an ``error_ignored`` custom attribute for every ignored error. This custom attribute can be used in the following ways.

* Use ``SELECT * FROM TransactionError WHERE error_ignored IS True`` to find errors that should have been ignored, but are not. This may be due to a bug or misconfiguration in New Relic.

Additionally, a subset of ignored errors that are configured as ignored will also get ``error_ignored_class`` and ``error_ignored_message`` custom attributes.

* Using New Relic terminology, this extra error class and message data will live on the Transaction and not the TransactionError, because ignored errors won't have a TransactionError.
* Use these additional custom attributes to help diagnose unexpected issues with ignored errors.

.. _IGNORED_ERRORS settings and toggles on Readthedocs: https://docs.openedx.org/projects/edx-platform/en/latest/search.html?q=IGNORED_ERRORS

Logging ignored errors
-----------------------

Following the same documentation as for monitoring, you can also enable logging with or without a stack trace. This additional information may be useful for tracking down the source of a mysterious appearance of an otherwise ignored error.

More targeted scoping of errors
-------------------------------

The initial implementation only enables this functionality by error ``module.Class``. If you need to scope the monitoring/logging for a more limited subset, like for certain requests, the expectation would be to enhance and document these new capabilities.
