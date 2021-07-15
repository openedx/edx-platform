Extract python api from POST /api/enrollment/v1/enrollment handler
==================================================================

Status
------
Accepted


Decisions
---------

We will extract the core enrollment functionality present in the POST handler for
    `POST /api/enrollment/v1/enrollment`
into a non-REST Python method while leaving functionality intact


Context
-------

edx-enterprise bulk enrollment use case currently invokes this endpoint once per learner + course
which leads to a large number of REST api calls in a short period thus hitting rate limits.


Consequences
------------

None expected on existing clients, since it's a refactor. But installed apps like edx-enterprise can now
avoid making REST API calls to LMS for enrolling one user in one course run.

Alternatives considered
-----------------------

Write a new endpoint in edx-platform that can handle bulk enrollment in a single REST invocation.
Since an existing bulk_enroll endpoint does exist in edx-platform writing a new one is not sensible.

Use the existing bulk_enroll endpoint that exists in edx-platform somehow. This endpoint cannot be
used as is, and we will still need to handle enterprise-specific concerns.

Add batching and pause between batches in the existing edx-enterprise codebase. This will
avoid the too many requests per unit time. But it involves adding pauses in a request cycle. This
is not ideal for user experience.
