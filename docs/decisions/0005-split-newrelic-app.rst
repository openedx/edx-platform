Split NewRelic App
******************

Status
======

Accepted

Context
=======

When using NewRelic, edx-platform as a monolithic APM app has the following issues:

* Errors or other data can get lost in Overview due to the number of different types of transactions
* Overview is not helpful for most teams that care about different parts of the app.

Decision
========

We will employ a "hacked" solution to set the NewRelic app name per transaction. This is considered a reasonable "hack" by NewRelic, but NewRelic dashboards are their more general recommendation.

We will define the mappings from request path to new app name in code. This mapping handler can be configured using a new setting, ``NEWRELIC_PATH_TO_APP_NAME_SUFFIX_HANDLER``.  The handler should take a request path and return None for the default mapping, or a suffix to be appended to the default app name. Providing the mapping as a setting enables quick rollback, and enables mapping overrides for the Open edX community.

Consequences
============

In order for this solution to work, we must disable gunicorn instrumentation. This prevents the transaction and app name from being set before reaching Django. This means that NewRelic will no longer provide data for gunicorn, and we will need to ensure that this data is monitored appropriately in other ways.

Additionally, the mapping code from request path to NewRelic app name happens before the transaction is initiated, and the time taken for the mapping is **not** accounted for in the transaction time. We will ensure this code performs well via unit tests.

Rejected Alternatives
=====================

Defining mapping code in config
-------------------------------

Defining the mapping code in code, rather than in config directly, has the following pros/cons::

**Pros:**

* Enables unit tests for correctness
* Enables unit test for performance of mapping code
* Uses simple config (i.e. a string, rather than a complex object)

**Cons:**

* Updated mapping requires code change rather than config change
* Enabling rollback requires multiple mapping handlers

Defining mapping during routing
-------------------------------

In the future, with Kubernetes, it may make sense to provide this mapping in the same place as other url routing. We could consider spinning up different containers for each desired mapping, which would enable gunicorn intrumentation, and might be closer to a more traditional use of NewRelic.

Because we are not yet using Kubernetes, this type of solution is premature at this time.

Using NewRelic custom dashboards
--------------------------------

The out-of-the-box dashboard for NewRelic APM provides us much of what we need today with no additional work. There are some features of NewRelic that can only be done at the application level, like bounded alerts. In the future, as we get better at other types of alerting and creating custom dashboards, we can revisit this decision if necessary.
