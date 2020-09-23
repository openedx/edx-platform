Discussions Plugin API
======================

Status
------

Proposal

Context
-------

Currently the Open edX platform provides its own discussions experience,
using a form tool that ships with the platform and is well integrated
into it. There is a common need to support other, external discussion
tools into the platform.

To make it possible for the platform to support integration with other
discussion tools, this ADR proposes a system for a new type of plugin
that allows extending the platform by adding other discussion tools
that can integrate more closely with the platform.


Decision
--------

We can enable a new type of plugin, a discussion app, that will provide
a standard interface that will hook into different parts of the platform
using standard APIs. New internal python APIs will also be created to
cater to the specific needs of discussion tools.

The platform with load a new type of plugin exposed via the
`openedx.discussion_apps` entrypoint. These plugins can be configured
and linked to a learning context using the new discussion configuration
APIs added in https://github.com/edx/edx-platform/pull/24190.

If a particular discussion plugin is linked to a course, then the
platform will load that plugin, and call the desired API in the plugin.
For instance, the plugin may provide a view to render for the course
tab for discussions, and another view to render for in-context
discussion instances.

The plugin can also hook into platform events such as a new user
registering in a course, which the plugin can use to create a synced
user account for the discussion tool, and set up proper groups and
permissions for the user if needed.

The plugin can expose signals for when new threads or comments are
posted, or content is followed or flagged.

An optional base class is provided for such discussion apps. This class
can serve as a reference for plugin developers. A plugin class will need
to provide at least some bare minimum attributes and methods to work
as a discussion tool provider. This class will be interface through
which the platform will integrate and interact with the plugin.

The initial implementation allows providing an internal name, and a
friendly name, a list of capabilities, a view to render in the course
tab, a view name for the tab content, and an `is_enabled` method that
allows enabling/disabling the plugin for a particular
request/context/user.

Not all plugins can (or will) support all the features that the internal
forums do. A plugin can declare a set of capabilities, such as whether
it supports LTI, in-context discussions, is accessible, or
internationalised etc via an attribute called `capabilities`, this list
will be used to create a comparison view of different tools during
course setup.

The intention is to support a way to override/extend this list so that
an Open edX instance can focus on the key attributes they find
interesting to expose. 
