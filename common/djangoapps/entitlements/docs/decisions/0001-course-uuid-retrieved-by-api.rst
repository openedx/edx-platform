1. Course UUID Retrieved from Discovery by API
----------------------------------------------

Status
------

Accepted

Context
-------

Course UUID is a more reliable and consistently unique identifier for a Course.


Decision
--------

The decision was made for consistency to not move the course UUID into the Platform data model.  As a result the only
method available to get a Course UUID based on a Course Key is the Discovery Service.

Consequences
------------

When there is a need to find a Course by UUID, but only the Course Key is available the Discovery API is required to
resolve the identifier.

References
----------

* https://openedx.atlassian.net/wiki/spaces/LEARNER/pages/171180253/Program+Bundling
