Score Override Audit Trail
--------------------------

`Jira issue <https://openedx.atlassian.net/browse/EDUCATOR-4295>`_

Status
======

Proposed (May 2019)

Context
=======

For the sake of auditing and accountability, we want to record which instructor overrode a problem score,
particularly for bulk operations like `Staff Graded Points <https://github.com/edx/staff_graded-xblock>`_. 
We want to be able to query for each instance of an override, even if this feature is not exposed in any UI.
Scores are currently stored in the Courseware Student Module model – a table which has grown to an enormous size
on edx.org. Adding a column to this table would be prohibitively expensive. 

Decisions
=========

* We'll add a new ``ScoreOverrider`` model with a foreign key to ``StudentModule``, which will record:

    * ``module_id``
    * ``user_id``
    * ``created`` (creation date)
* For bulk operations on scores, we'll create a new row in this table.
