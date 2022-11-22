Discussions
===========

This Discussions app is responsible for providing support for configuring
discussion tools in the Open edX platform. This includes the in-built forum
tool that uses the `cs_comments_service`, but also other LTI-based tools.


Technical Overview
------------------

This app adds support for alternative Discussion providers, where a provider is
initially an LTI app that can be embedded in the discussion tab.

A list of supported providers is included configured in this app, with the
features each app supports, its support level, and other details that are
returned by the API and drive the UI for selecting and comparing providers in
the course authoring MFE.

Each context (course) has an associated `DiscussionConfiguration` object that
specifies the provider to use for that course, and includes other configuration
information for the course. For LTI-based providers, it's also linked to an
`LtiConfiguration` entry.

The `plugin_configuration` field on this model is to store
provider/plugin-specific configuration that won't make sense for other plugins.

Different parts of the course can be linked to different discussion topics. The
standard use case here to have a topic for each Unit in the course. The
`DiscussionTopicLink` model handles this association, and links a particular
usage key in a particular course to a topic.

The new Discussion API is driven entirely by these `DiscussionTopicLinks` in
the database, so it's possible to have a third-party plugin that changes how
and where these topic links are created.

When a course is published, the `listen_for_course_publish` signal handler is
called, and this signal in turn calls the
update_discussions_settings_from_course_task` in the background.

That task goes through the module store and builds a
`CourseDiscussionConfigurationData` object that has all the relevant course
discussion configuration information such as the course key, the provider type,
whether in-context discussions are enabled, whether graded units are enabled,
when unit level visibility is enabled. Other plugin configuration and a list
of discussion contexts for which discussions are enabled. Each discussion
context has a usage key, a title (the units name) an external id
(the cs_comments_service id), it's ordering in the course, and additional
context. It then sends its own signal that has the discussion configuration
object attached.

Finally, the handler for this discussion change signal, takes the information
from the discussion change signal and compares it to the topics in the
database, and does the following:

- If it sees discussions contexts (units) without topics it creates new topics
  link entries for the new units. This will happen if you create a new unit,
  or enable discussions for a unit that previously had them disabled.

- If it sees discussion topics without contexts it disables/archives them.
  This could happen when a unit is deleted or if a unit that previously had
  discussions enabled, now has discussions disabled.

- If it sees any other change, i.e. unit name change etc. it applies that
  change to the database as well.

