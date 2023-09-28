0003: Hybrid approach for public course authoring APIs
======================================================

Context
-------

We are planning to offer public APIs via oauth that allow course authors to create
and update course content via an external application. The plan for this is outlined in this
`Spec Demo`_.

.. _`Spec Demo`: https://openedx.atlassian.net/wiki/spaces/COMM/pages/3696066564/Spec+Memo+API-Based+Management+of+edX+Course+Blocks+Outlines+and+Settings+MVP.

Rather than restricting a course to only ever be editable either via API or manually,
we will offer a hybrid solution where both are possible.

A hybrid solution faces two challenges:

- "out-of-date write conflicts": how do we handle a situation where an API user attempts to update
  a course using a stale course snapshot as a starting point?
  This creates a danger of overwriting another person's changes.
- "dirty writes": how do we handle a situation where there are multiple concurrent, asynchronous import or update 
  operations that may be in conflict with each other?

Some considerations that come into play when picking an approach are:

1. Having the system reliably play traffic cop isn't simple, principally because of our reliance on slow-running async tasks.
2. Even if we ignore the problem of playing traffic cop, embracing hybrid editing means clients need some way to know
   whether other users have made changes.

We analyzed a range of the most viable options to handle these challenges.
We ruled out any we found to be much too risky or much too hard to implement due to a high amount of complexity.
That left us with three alternatives, of which we rejected the following two:

- adding a toggle that lets users switch the course between enforcing only manual editing
  and only API editing. This toggle needs to allow for running import operations to finish before switching, thus making it complex.
- using a form of optimistic concurrency control where we expect different users and explicitly version each change, then forbid
  any API operation unless the API operator provides a version identifier that is not out of date.

We rejected these challenges on the basis that they were complex to implement and make us play "Traffic cop".

However, future iterations on the API may require us to be more strict and employ further safeguards, and it remains a possibility to circle
back and add one of these options on top of what we do now initially.

Another complication is that our planned solution is limited in terms of rollback capabilities: xblocks are internally versioned
and we can use this internal versioning to offer rollback tools, and this extends to rolling back changes to their tree structure
(for example adding subtrees, reordering child xblocks, etc). However, other files that are imported, like static assets and some course-level
configuration, do not have this versioning capabilities. According to our planned architecture around these APIs, we will not support versioning
and rollback on our side. Instead, we expect users to handle this problem themselves by having backups and version control for these files independently.

We also do not offer any draft capabilities for the API; changes will be immediately published.

Decision
--------

- We consider the user responsible for avoiding, resolving, or fixing conflicts.
- Courses that are operated in this hybrid fashion - that is, they are being edited not just via studio, but also via API -
  are intended to be edited by one user at a time. In the API documentation, we will ask users to follow this principle.
- While we don't plan to enforce this prohibition of concurrent users today, leaving it as a self-policing responsibility users bear,
  we leave open the option of doing so in the future..
- We provide logs about past changes to the user to alert them of other users' changes.
- We provide sufficient rollback tools to fix any problems with xblocks / xblock structure the users may have caused.
  Provided that modulestore versioning makes older versions of an XBlock available, we will provide a programmatic way to replace the current version
  of an XBlock with an older version, referenced by version ID.
  Our current goal is to offer this packaged as a "undo task" operation.
- We do not provide any versioning, rolling back, or logging for anything that is not an xblock (static assets,
  course-level policies and settings, etc). We recommend that the users employ version control for this on their side.

Consequences
------------

The decision not to enforce a limit of one client at a time means that users may run into conflicts or problems if they
do not follow our instruction to work one at a time and coordinate.
Because no rollback capabilities are offered by the API for course assets, the burden of maintaining assets under external
source control falls on the user; a user's failure to do so may lead to irrevocable content loss on course corruption.

With this decision, we make clear where the responsibility lies for dealing with problems. We do not have to
build a complex mechanism to avoid or resolve conflicts ("playing traffic cop");
and consequently, we do not need to act on any errors that happen when this mechanism isn't perfect.

However, there may very well arise the needs to add safeguards in the future. The most straightforward and simple action would be to
actually enforce this one-concurrent-user policy and not allowing more than one user to edit concurrently.
