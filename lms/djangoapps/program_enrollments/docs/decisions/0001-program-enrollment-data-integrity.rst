ProgramEnrollment Model Data Integrity
--------------------------------------

Status
======

Accepted (circa August 2019)


Context
=======

For the sake of fundamental data integrity, we are introducing 2 unique
constraints on the ``program_enrollments.ProgramEnrollment`` model.

Decisions
=========

The unique constraints are on the following column sets:

* ``('user', 'program_uuid', 'curriculum_uuid')``
* ``('external_user_key', 'program_uuid', 'curriculum_uuid')``

Note that either the ``user`` column or the ``external_user_key`` column may be null.
In the future, it would be nice to add a validation step at the Django model layer
that restricts a model instance from having null values for both of these fields.

Consequences
============

The first constraint supports the cases in which we save program enrollment records
that don't have any association with an external organization, e.g. our MicroMasters programs.
Non-realized enrollments, where the ``user`` value is null, are not affected by this constraint.

As for the second constraint , we want to disallow the ability of anyone to register a learner,
as identified by ``external_user_key``, into the same program and curriculum more than once.
No enrollment record with a null ``external_user_key`` is affected by this constraint.

Together, these constraints restrict the duplication of learner records in a specific
program/curriculum, where the learner is identified either by their ``auth.User.id`` or
some ``external_user_key``.

This constraint set does NOT support the use case of a single ``auth.User`` being enrolled
in the same program/curriculum with two or more different ``external_user_keys``.  Supporting
this case leads to problematic situations, e.g. how to decide which of these program enrollment
records to link to a program-course enrollment?  If needed, we could introduce an additional
set of models to support this situation.
