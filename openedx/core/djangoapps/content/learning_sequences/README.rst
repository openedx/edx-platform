==================
Learning Sequences
==================

This package creates a ModuleStore-independent representation of learning
sequences (a.k.a. "subsections" in Studio), as well as how they are put together
into courses. It is intended to serve metadata about Learning Sequences to end
users through the LMS, though it is also available to Studio for pushing data
into the system. The first API this app implements is computing the Course
Outline.

---------------
Direction: Keep
---------------

This package is being actively developed, but in a very early state. We're not
going to start feeding data into it (by triggering off of publish) until it's a
little more complete, so that it's easier to make drastic changes to the data
model if necessary. During development, you can seed data into it by using the
``update_course_outline`` management command.

-----
Usage
-----

* You may make foreign keys to learning_sequence models from your own app.
* You may refer to data structures defined in
  ``openedx.djangoapps.content.learning_sequences.api.data``.
* Otherwise, you should only ever import and use functions from the top level
  ``openedx.djangoapps.content.learning_sequences.api`` package. Do not import
  from anywhere else in the package, including sub-modules of ``api``.

----------
Motivation
----------

We already have ModuleStore and Block Tranformers, so why create yet another way
to access course structure data? Isn't that going to cause bugs because access
rules will have to be reimplmented–as we've already seen with mobile APIs?

1. To enable more dynamic courseware, we're shifting responsibility for
   course structure and navigation out of ModuleStore/XBlock. We are keeping OLX
   compatibility, but eventually the LMS XBlock runtime would only be invoked at
   the Unit level and below.
2. Block Transformers operate on the entire course at one time, and lack the
   kind of granular database models we'd want for quick lookups of metadata for
   a single sequence.
3. Block Transformers are extremely powerful, but also complex and slow.
   Optimizing them to suit our use case would be a lot of work and result in
   even more complexity. Sequence and outline related metadata is much smaller,
   and we can make simplifying assumptions like treating the outline as a tree
   and not a DAG (i.e. each Sequence being in only one Section).

--------------
How to Extend?
--------------

This app is experimenting with some new conventions, so please read the decision
docs (``docs/decisions``). Many of the modules also have a long top-level
docstring explaining what they should be used for–please read these. Many of the
conventions are there to promote predictable behavior and are dramatically less
effective if broken even in little ways.

I want to add more data to the public API.
==========================================

The public data types are in ``api/data.py``. Database persistence is in
``models.py`` like all Django apps, but our Django models are extremely thin and
dumb. All real business logic should happen in a module within the ``api``
package. Currently, all the existing API logic is handled in ``api/outlines.py``
and re-exported at the top level in ``api/__init__.py``. If your new
functionality is outlines related, please follow this convention. Otherwise, you
can create a new module in ``api/`` (e.g. ``api/sequences.py``) to hold your
logic, and re-export that via the top level ``api/__init__.py``.

I want to add a new rule affecting how sequences show up in the outline.
========================================================================

You probably want to create or modify an OutlineProcessor (``api/processors``).
This is not yet a pluggable interface, though it was designed to make it easy to
turn into one. Please see the docstrings in ``api/processors/base.py`` for
details on how to write one.

I want to pull data from ModuleStore or Block Structures.
=========================================================

Making any synchronous calls to these systems will break the performance goals
of this app. If you need data from these systems, please find a way to push that
data into smaller mdoels at course publish time.
