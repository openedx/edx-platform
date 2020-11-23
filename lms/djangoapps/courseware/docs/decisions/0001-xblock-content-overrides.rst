1. XBlock Content Replacement for Access Control
================================================

Status
------

Accepted

Context
-------

Content Type Gating requires that users be prevented from viewing
or interacting with an XBlock, and instead being shown a message
suggesting how to gain access. XBlocks are rendered in a tree,
and the rendering is managed by the XBlocks themselves. XBlocks
expect to be able to retrieve their own children, inspect attributes
of those children, and then render those children w/ a method call.

XBlock access control removes a child from the render tree, which
makes it difficult to know where to generate the replacement message
during rendering. Substituting one xblock for another of a different
type at runtime has historically problematic, because the different
XBlock types don't behave the same way. Replacing an XBlock with a
non-XBlock type is difficult for the same reason.

Decision
--------

We will continue to manage access-control decisions using ``has_access``.
When access is denied, we will generate a custom ``Fragment`` containing
the error message, and attach it to the ``AccessResponse`` object.

While rendering the XBlock hierarchy, we will continue to check access
as is currently implemented. If the ``AccessResponse`` returned has a
user-facing error fragment (stored in ``AccessResponse.user_fragment``),
then we will act as though the XBlock was not access restricted, and
allow it to be loaded.

In order to actually restrict access to the XBlock, we will add an
``xblock_wrapper`` that will again check whether a user has permission
to view the xblock. If the user doesn't, and the ``AccessResponse``
has a ``user_fragment`` set, then that content will be substituted
for the XBlock's originally rendered ``Fragment``.

Consequences
------------

XBlocks can be access-limited with custom user-facing messaging.
There is a performance cost to those messages, because the XBlock
that is being access-limited will still render its own ``Fragment``.
