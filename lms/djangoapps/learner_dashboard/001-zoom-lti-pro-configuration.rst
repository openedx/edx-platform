Configure Zoom Lti in Programs
--------------

Status
======

PENDING

Context
=======

The zoom lti pro is needed to be configured for programs (both masters and
regular) to provide video call feature. zoom-lti-pro can be installed by any
user for free to get credentials which can be used to configure as LTI.
But there is no specified  model that can be used to map zoom LTI credentials
with programs.


Decisions
=========
We can use the ``program_discussion_configuration`` model to add zoom lti pro
configurations for the program. A new type will be added so we can identify the
type of configuration if it is a discussion or live configuration.


Consequences
============

It would become possible to add zoom lti configurations in programs with
minimal effort.


Alternatives
============

1.  New model ``program_live_configuration`` can be created which will allow us
    to map LTI credentials to programs.
2.  ``program_discussion_configuration`` model can be renamed to a more generic
    name like ``program_lti_configuration`` but it will require major
    refactoring of code.
