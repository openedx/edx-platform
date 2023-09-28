Gradebook User Interface and Experience
---------------------------------------

Status
======

Proposed

Context
=======

We are implementing a "Writable Gradebook" feature from the instructor dashboard.  For additional
background see 0001-gradebook-api_.

.. _0001-gradebook-api: 0001-gradebook-api.rst

Decisions
=========

#. **Don't display non-graded sections**

   a. Any subsections that are marked as ``graded: false`` will not be displayed in the UI.  This allows
      us to ignore problems where such sections don't possess a ``label``.

   b. We will eliminate the `comment` column/field in the modal that allows a user to edit grades.  We currently
      have no model in which such data can be stored.
