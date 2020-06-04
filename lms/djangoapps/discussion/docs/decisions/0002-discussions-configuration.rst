2. Discussions Configuration API
================================

Context
-------

The current cs_comments_service is configured with the main platform, and has
minimal course-level configured requirements. Once Open edX is open to other
discussion platforms there will be need for configuring such platforms in a way
that allows course authors to pick from a pre-set list of configuration options
when setting up a course.

Decision
--------

A new configuration system will be implemented for course apps that allow people
with the correct permission levels to create a configuration object that can
be used in different scopes.

For instance, a configuration object tied to a site will be available to all
course authors on that site to use when configuring discussion for a course. A
configuration object tied to a site and org will be available to for use
for all courses in that org.

A configuration object has to at least specify a site, and can at most specifiy
a site, and org and a learning context. In this case it will only be available
to for that particular learning context.

When a configuration is selected for a particular course, a link to that unique
configuration id will be created for that course run. The configuration can then
be changed and will be auto-updated everywhere it is used (i.e. in case a
password or other secret needs to be changed).

This configuration link will allow overriding settings if needed for a
particular course run without propagating to other instances of the same
configuration.

For someone creating a course, they will simply see a list of configuration
options for different discussion tool providers that have been configured for
their access level, and can select one of them.

Consequences
------------

On the simplest side a site administrator can set up a single configuration that
all future courses can use. For a more complex setup configuration objects can
be created with multiple levels of access such that only courses within a
particular org/course have access to particular configuration options.
