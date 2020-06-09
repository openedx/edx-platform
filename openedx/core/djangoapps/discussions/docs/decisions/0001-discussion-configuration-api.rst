Discussion provider configuration
=================================

Status
------

Proposal


Context
-------

During the development of discussions plugins, a need arose for a system of
configuration that would allow admins to configure connections to different
discussion tools, and have course authors select an established configuration
without requiring admins to share any secrets with course authors.

For example, a discussion tool provider might require admins to specify OAuth2
credentials that will be needed to integrate their tool with the platform. This
needs to be configured by an admin, and used by a course, but ideally course
authors should not have access to this information.

It would also be useful to have multiple sets of configuration for different
discussion tools. A course creator can then select one of the available
configurations based on their requirements.

For instance an organisation might be using a particular Discourse instance
across a number of their courses. So an admin will create a new configuration
object that specifies all the settings the Discourse plugin needs to operate,
such as the site location, the auth credentials etc. When setting up a new
course, a course author will then be able to see this as one of the possible
options when configuring Discourse as the discussion tool.

Additionally, we might want to prevent certain configurations to be available
to all courses on a site. So it would be useful to limit configuration options
to a specific site, or Organization.

This ADR proposes a new configuration system that allows admins to create
pre-populated configurations for specific discussions providers, which can then
be used and optionally overridden by course authors/admins.

Decision
--------

We can create two models, `DiscussionProviderConfig` and
`LearningContextDiscussionConfig` that together provide the functionality
described above.

The `DiscussionProviderConfig` model stores a configuration name (this will be
visible to course authors configuring a discussion tool), a provider (this will
be the id of the plugin for which the configuration is defined), and a config
JSON field (this will store the actual config). A configuration can be also be
restricted to only be visible/available for a specific site, or org by setting
`restrict_to_site` or `restrict_to_org`. Only one of these can be set at a time
and if set only courses on that site, or that org can see the configuration as
an option. Changes to this model are tracked using Django Simple History.

To actually use a configuration for a particular course, we use the
`LearningContextDiscussionConfig` model. This will link a course to a particular
config. There is the ability to override the configuration for a particular
course if needed using the `config_overrides` JSON field.

To disable discussions for a course, it is possible to set the `enabled` field
on this model to false. If such a object isn't linked to a provider config then
it is considered to be disabled.
