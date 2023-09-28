Matriculation on UserSocialAuth Changes
---------------------------------------

Status
======

Accepted (circa October 2019)


Context
=======

Georgia Tech has been enrolling learners into its Master's programs
for a long time, using enterprise-oriented APIs for the purpose. To
transition them to using our Master's-intended workflow, we've worked
out a plan with them to convert existing ``UserSocialAuth`` records to use
a different SAML-provided field as the canonical UID used elsewhere in
our system to identify the learner for program enrollment
purposes. Thus, we've already decided we'll need a one-time management
command to update these learners' User SocialAuth records to use the
new UID.

The scope of this decision is a particular snag in how program
enrollments are linked to learner accounts. Namely, this linking only
occurs on the creation of a ``UserSocialAuth`` record, and not in
response to the kind of update we're proposing to perform with our
management command.

Decisions
=========

To address this concern and to achieve greater flexibility of program
enrollments into the future, we will attempt to link program
enrollments to learner accounts upon any change to a
``UserSocialAuth`` record, rather than solely on creation.

Consequences
============

This may have a performance impact, since updates to
``UserSocialAuth`` records happen often at times which would not
benefit us. We anticipate this performance impact will be fairly
minimal given the current indices on the table, however.

This does enable us to keep the management command simple. It also
enables us to re-trigger program enrollment linking on demand by
making trivial changes to the ``UserSocialAuth`` record, which may be
helpful for support purposes.

Alternatives
============

We also considered, but rejected the following possibilities:

1) Switch our ``post_save`` signal handler to ``pre_save``, and diff
   the model fields on updates to determine whether we've changed the
   UID.
2) Make the management command more complex, and have it call the
   program enrollment-linking code itself rather than relying on these
   signals.
