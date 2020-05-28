Monitoring by Owner
*******************

Status
======

Accepted

Context
=======

It is currently difficult for different teams to have team-based on-calls rotations, alerting and monitoring for various parts of the edx-platform (specifically LMS).

Decision
========

We will implement a custom metric "code_owner" that can be used in NewRelic (or other monitoring solutions that are made pluggable).

Ultimately, to minimize maintenance, the value of the "owner" metric should be populated using the source-of-truth of ownership of various parts of edx-platform.

See `Rejected Alternatives`_ for details of the decision **not** to split the NewRelic application into multiple NewRelic applications.

Note: "owner" is a MySql reserved word, which NewRelic cautions against using, so we are using "code_owner".

Consequences
============

This metric should be quickly available for use with custom alerts and custom dashboards.

In the future, this metric could potentially be added to logging as well.

Rejected Alternatives
=====================

Splitting the NewRelic application
----------------------------------

The edx-platform (LMS) NewRelic application could have been split into multiple applications. This would have had the benefit of getting the out-of-the-box APM Dashboards for free.

We decided against this alternative because:

* To enable this solution, we would need to disable gunicorn instrumentation, and this instrumentation has proved to be valuable for understanding certain types of production issues.
* Splitting the app may make it more difficult to pinpoint the source of any problem that affects multiple applications.
* The application splitting depends on a slight "hack" from NewRelic, by resetting the application name for each path.

  * This "hack" goes against the grain of NewRelic's typical recommendations, so there could be unknown pitfalls.
  * The mapping of request path to owner would require additional maintenance.
  * Mapping time is **not** accounted for in the transaction time.
