Open edX: Built-in XBlocks
--------------------------

This area is meant for exceptional and hopefully temporary cases where an
XBlock is integral to the functionality of the Open edX platform.

This is not a pattern we wish for normal XBlocks to follow; they should live in
their own repo.

Discussion XBlock
=================

This XBlock was converted from an XModule, and will hopefully be pulled out of
edx-platform into its own repo at some point.  From discussions, it's not too
difficult to move the server-side code , but the client-side code is used by
the discussion board tab and the team discussion, so for now, must remain in
edx-platform.
