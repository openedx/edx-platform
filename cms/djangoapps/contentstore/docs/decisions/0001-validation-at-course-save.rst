========================================
OEP-0001: Data Validation at Course Save
========================================

.. list-table::
   :widths: 25 75

   * - OEP
     - :doc:`OEP-XXXX </oeps/oep-XXXX-YYYY-ZZZZ>`

       * <XXXX is the next available OEP number>
       * <YYYY is the abbreviated Type: proc | bp | arch>
       * <ZZZZ is a brief (< 5 words) version of the title>
   * - Title
     - <OEP title>
   * - Last Modified
     - <date string, in YYYY-MM-DD format>
   * - Authors
     - <list of authors' real names and optionally, email addresses>
   * - Arbiter
     - <Arbiter's real name and email address>
   * - Status
     - <Draft | Under Review | Deferred | Accepted | Rejected | Withdrawn | Final | Replaced>
   * - Type
     - <Architecture | Best Practice | Process>
   * - Created
     - <date created on, in YYYY-MM-DD format>
   * - Review Period
     - <start - target end dates for review>

Context
-------
Data validation in the Django Rest Framework "is performed entirely on the serializer class". Doing validation at
the serializer level provides a few key advantages, such as making the data validation code easier to understand and 
reason about.

The Advanced Settings view is a Django view that allows reading and writing course metadata to the modulestore. These data
proctored exam settings (e.g. "enable proctored exams", "proctoring provider", etc.). This view leverages the CourseMetadata class
to read from and write to the modulestore. The CourseMetada class supports data validation in the validate_and_update_from_json method.
The results of calling this method can be saved to the database.

We are adding a Django Rest Framework REST API that exposes an endpoint for reading and writing proctored 
exam settings to the modulestore. This REST API will be used by the course-authoring MFE to support a new
Proctored Exam Settings page.

Decision
--------

We will not implement additional validation 

Consequences
------------

This section describes the resulting context, after applying the decision.
All consequences should be listed here, not just the "positive" ones. A particular
decision may have positive, negative, and neutral consequences, but all of them
affect the team and project in the future.

References
----------

List any additional references here that would be useful to the future reader.
See `Documenting Architecture Decisions`_ for further input.

.. _Documenting Architecture Decisions: http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions
