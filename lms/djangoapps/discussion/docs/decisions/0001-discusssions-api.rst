1. Discussions API for discussions plugins
==========================================

Context
-------

The cs_comments_service is currently the only way to natively enable
discussions in Open edX. There is a need to provide a standard way for external
forum/discussion tools to plug into the platform and seamlessly provide
discussion capabilities.

While different tools will have different level of capabilities and will
differ greatly in their level of integration and how seamless that integration
is, ideally this API should provide enough tools to enable the same level of
integration that is available via cs_comments_service.

Decision
--------

The current discussion application will no longer just host cost to support the
native Open edX forum, but also enable support for other forum tools.

To enable this, all code related to cs_comments_service will be moved out to a
separate package outside 'lms.djangoapps.discussion', to an internal or
potentially external plugin.

This discussion app will then provide a set of core APIs and capabilities that
any discussion integration tool can use to integrate with the platform.

Generally the discussion app will manage links between internal and external
users, internal and external roles, and internal and external ids for particular
instances of a discussion tool.

The discussion plugin will handle the actual interaction with the external
platform. For instance, while the discussion app will maintain a link between
internal and external user ids, the discussion plugin will manage the actual
creation of an external user using the APIs provided by the external tool.

Core platform APIs available to plugins:

- Getting a user from an external ID
- Getting a group from external ID
- Getting a user's groups
- Getting a user's permission/access
- Signals to call for creation of threads, comments, follows etc.
- A new signal will trigger when a course discussion tool is changed
- Getting the configuration for discussions for a particular course

The plugin will provide APIs to:

- Create a new user
- Update an existing user
- Retire an existing user
- Create a new user group
- Add an existing user to an existing group
- Create a new discussion context (this could be linked to a thread/category/forum etc)
- Get an embeddable view for a particular context (could be a thread/category/forum etc)
- Get a settings view for configuration.

Consequences
------------

Developers can create and support external discussion tools, which can then be
configured and used natively in the platform.
