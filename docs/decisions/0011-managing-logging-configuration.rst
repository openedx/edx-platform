Status
======

Draft


Context
=======

Logging configuration needs more options to be useful for devops/SRE work.

Decision
========

Let us add an optional override dictionary to `get_logging_config`. This would
allow us to change filters, log options, and add custom log handlers, with
varying utility for differing edx platform installations.

Specification of the override dictionary can be done within the YAML configs,
to keep things consistant with how the rest of managing Django settings.

Explanation and examples for adding logging customization to Django settings
should be included in any relevent documentation.


Consequences
============

Having the override logging settings defined in yaml override files keeps
changes to log configuration easier to view and manage, as they will be
consistent with the rest of Django setting management.

Having the actual override occur as part of `get_logging_config` means one does
not need to worry about resetting the logging state, if called multiple times
during setting extensions.

The limitation demarkation of log configuration then lies in what the logging
module actually offers.


Alternatives Considered
=======================

Individual kwargs for specific overrides
----------------------------------------

The argument here is to create limitiation by attempting to guess what specific
logging customization might be required for future log formating. This would
clutter the interface if more options are later discovered to be necessary.

Moving the log configuration into the settings module
-----------------------------------------------------

The argument here is to make logging management the same as other configuration
values, for ergonomics. There are advantages to this; the implementation does
not need to handle dictionary merges, and the possibility of divergent logging
implementations is less. But the initial comment to the implementation is worth
reproducing in full here:

    Return the appropriate logging config dictionary. You should assign the
    result of this to the LOGGING var in your settings. The reason it's done
    this way instead of registering directly is because I didn't want to worry
    about resetting the logging state if this is called multiple times when
    settings are extended.

This seems like a good enough reason to continue to use `get_logging_config`.

