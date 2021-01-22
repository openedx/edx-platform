One Anonymous User Id per user, course_id pair
----------------------------------------------


Status
======

Accepted

Context
=======

Previously, whenever the SECRET_KEY was changed, anonymous_id_for_user function would return a different id. This caused effects of changign SECRET_KEY to be non-trivial. Specifically, there would be a loss of tracking continuity in external systems for an user, course id pair. We hope to diminish downstream affects of chaning SECRET_KEY.


Decision
========

It was decided that the anonymous_id_for_user function should return the priviously calculated anonymous_user_id if it already exists in database.

Consequences
============

The implementation of this decision results in there being only one anonymous_user_id per user, course_id pair.
