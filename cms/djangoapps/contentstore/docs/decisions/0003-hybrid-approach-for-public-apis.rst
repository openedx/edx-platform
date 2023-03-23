0003: Hybrid approach for public course authoring APIs
======================================================

Context
-------

We are planning to offer public APIs via oauth that allow course authors to create
and update course content via an external application. The plan for this is outlined in this
`Spec Demo`_.

.. _`Spec Demo`: https://openedx.atlassian.net/wiki/spaces/COMM/pages/3696066564/Spec+Memo+API-Based+Management+of+edX+Course+Blocks+Outlines+and+Settings+MVP.

Rather than restricting a course to only ever be editable either via API or manually,
we will offer a hybrid solution where both is possible.

A hybrid solution faces two challenges:

- "out-of-date write conflicts": how do we handle a situation where an API user updates course content,
  yet there is an implicit conflict because a manual user edited the course recently and now the API user's local files are outdated?
  This creates a danger of overwriting another person's changes.
- "dirty writes": how do we handle a situation where there are multiple asynchronous import or update operations
  at once that may be in conflict with each other?

Some considerations that come into play when picking an approach are:

1. Having the system reliably play traffic cop isn't simple, principally because of our reliance on slow-running async tasks.
2. Even if we ignore the problem of playing traffic cop, embracing hybrid editing means clients need some way to know
   whether other users have made changes.

We analyzed a range of the most viable options to handle these challenges.
We mainly rejected two alternatives, although there are many options:

- adding a toggle that lets users switch the course between enforcing only manual editing
  and only API editing. This toggle needs to allow for running import operations to finish before switching, thus making it complex.
- using a form of optimistic concurrency control where we expect different users and explicitly version each change, then forbid
  any API operation unless the API operator provides a version identifier that is not out of date.

We rejected these challenges on the basis that they were complex to implement and make us play "Traffic cop".

However, future iterations may require us to be more strict and employ further safeguards, and it remains a possibility to circle
back and add one of these options on top of what we do now initially.

Decision
--------

- We consider the user responsible for avoiding, resolving, or fixing conflicts.
- Courses with a registered API user are intended to be edited by one user at a time. This will be included in the API documentation.
- We leave open the option to enforce this restriction to one concurrent user in the future.
- We provide logs about past changes to the user in order for them to know whether other users have made changes.
- We provide sufficient rollback tools to fix any problems with xblocks / xblock structure the users may have caused.
- We do not provide any versioning, rolling back, or logging for anything that is not an xblock (static assets,
  course-level policies and settings, etc). We recommend that the users employ version control for this on their side.

Consequences
------------

Users may create conflicts or problems if they do not follow our instruction to work one at a time and coordinate.
We can only give them the tools to rollback changes and modifications to xblocks and the xblock structure, so there is an increased
risk of them causing problems with course-level settings or assets. If they do not version control on their own side, they need
to find other solutions to fix this.

This can be mitigated by adding more safety mechanisms later on, the most straightforward action being to
actually enforce this one-concurrent-user policy.

It is clear where the responsibility lies for dealing with problems. Choosing this option, we do not have to
build a complex mechanism to avoid or resolve conflicts ("playing traffic cop")
and then needing to act on any errors that happen when this mechanism isn't perfect.
