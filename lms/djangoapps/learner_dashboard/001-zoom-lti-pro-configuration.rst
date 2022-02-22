Configure Zoom Lti in Programs
--------------

Status
======

Approved

Context
=======

The zoom lti pro is needed to be configured for programs (both masters and
regular) to provide video call feature. zoom-lti-pro can be installed by any
user for free to get credentials which can be used to configure as LTI.
But there is no specified  model that can be used to map zoom LTI credentials
with programs.


Decisions
=========

New model ``program_live_configuration`` will be created which will allow us
to map LTI credentials to programs.

We are going ahead with LTI 1.1 to configure zoom for now due to some
constraints in current implementation.

Consequences
============

It would become possible to add zoom lti configurations in programs with
minimal effort.


Alternatives
============

1.  We can use the ``program_discussion_configuration`` model to add zoom lti
    pro configurations for the program. A new type will be added so we can
    identify the type of configuration if it is a discussion or live
    configuration.
2.  ``program_discussion_configuration`` model can be renamed to a more generic
    name like ``program_lti_configuration`` but it will require major
    refactoring of code.
