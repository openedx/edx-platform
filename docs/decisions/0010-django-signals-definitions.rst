Move definitions of Django Signals to an standalone library.
------------------------------------------------------------

Status
======

Proposed

Context
=======

The edx-platform Django project makes uses of several custom Django signals to report certain events that can be used by 
plugins or by other Djangoapps in the codebase. Since in the plugins, we don't have access to the Django Signals definitions made
in the edx-platform Djangoapps there is not an suitable way to use them in order to modify and extend the behavior of the platform.


Decisions
=========

1. The custom Django Signals used in the platform will be extracted and moved to a new python library tha
  the platform itself and the plugins can access the definitions using a similar approach.

Consequences
============

1. A library called openedx-hooks will be created to store the Django Signal definitions.
2. Old Django Signals defined in the platform should be deprecated using the normal conventions used by the platform.
3. New Django Signals that are candidates to be used in the platform by plugins should be created now using this new library.
