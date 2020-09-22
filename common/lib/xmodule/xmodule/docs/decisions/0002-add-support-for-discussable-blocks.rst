2. Add course field to enable discussions
-----------------------------------------

Status
------

Proposed

Context
-------

We want to support a new simplified way for configuring discussions in a
course, and allow plugins to extend the available options for discussions
providers. With this system in a place we will need a new way to specify
at a course run level if discussions are enabled.

Currently disabling


Decisions
---------

1. Create a global toggle for discussions in a course
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We can add a new field to the course block that enables/disabled discussion
integration at a course run level. If discussions are disabled for a course, no
discussions UI will show up for that course anywhere.

If discussions are enabled, then the discussion tool the course author selected
will show up wherever it supports being embedded (the course tab, and
in-context)


2. Allow blocks to mark themselves are discussable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this new approach we will allow blocks to mark themselves as discussable.
Any block that exposes a `is_discussable` field and this field in enabled will
have a discussion context associated with it (if the selected discussion tool
supports multiple discussion contexts/in-context discussions).

When the learning MFE encounters a block that has is discussable, it will fetch
the associated context and render it using the discussion tool.

3. Verticals will be discussable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The vertical block will include the `is_discussable` field allowing it to be
marked as discussable. This means that any vertical in a course can made
discussable.

4. The discussion block will be discussable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This might seem obvious, but by making the discussion XBlock compatible with
the new mechanism for marking discussions, it automatically migrates all
existing courses that have a discussion block to support the new mechanism for
supporting discussions.

5. There will be tools to bulk-mark verticals as discussable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To allow quick setting up of discussions in a course, there will be a
configuration UI that will allow marking all/some verticals in a course as
discussable.
