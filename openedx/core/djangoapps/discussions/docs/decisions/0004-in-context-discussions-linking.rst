Linking In-Context Discussions to Units
=======================================


Status
------

Proposal


Context
-------

As part of the BD-38 initiative (Blended Development, Project 38), we are
investigating a new way to set up discussions for a course that tries to
simplify the way discussions are configured and ties them more closely to the
course structure.

The first simplification that the new system makes is to remove the
discussions XBlock, and instead supports simply marking individual units
as discussable, in which case a discussion UI will show up in-context.

Currently this will only be supported for the edX Forums internal
discussion provider, but it could be extended in the future to support
other providers.

In addition to providing a way to mark Units as discussable, there will
also be a way to simply enable discussion for all units in the course.
One further control provided here will be to toggle discussions on or
off for graded discussions.

Finally, it will also be possible to group discussions at a Sequence
level instead of the Unit level.


Requirements
------------

In order to enable in-context discussions with the above features we
need a way to:

- Mark a Unit as discussable
- Store configuration options for discussions
- Automatically mark/unmark units as discussable when settings change
- Associate a unit with a corresponding discussion id
- Make this discussion ID available via an API


Consideration
-------------

Most of these configuration entries would be right at home in the
``DiscussionsConfiguration`` model in ``plugin_settings``, however since they need
to be available during course import-export, they should be stored in the
course object itself.

There is already a way to associate a discussion ID with a Discussion XBlock
using its usage key. This same mechanism can be used to associate a Unit usage
key with a corresponding discussion id.

However the current mechanism has a few issues. It is stored as a JSON
structure in the ``DiscussionsIdMapping`` model which has course id and a mapping
of the discussion id to the xblock usage key in a single dict.

This is OK for the existing setup because this is just a caching mechanism and
the source of truth for this mapping is the XBlock itself, which stores the
discussion id. On course publish this information is cached to
``DiscussionsIdMapping``.

For the new discussions system though, this mapping would be the source of
truth for the link between discussions and units, so we should use a model
where each such link is encoded as a row in the database.

Decision
--------

Since the discussions settings need to be stored in the course structure we
should create a new JSON structure in the course that matches the structure
of ``plugin_settings``. This can then be used to store not just the settings
for the inbuilt discussions provider, but for any discussions provider in the
future.

When a course is published, we can copy over all the ``plugin_settings`` to the
course in a JSON field called ``discussions_settings`` with the following
structure:

.. code-block:: JSON

    {
        "discussions_enable_in_context": bool,
        "discussions_enable_graded_units": bool,
        "discussions_custom_visibility": bool,
        "edx-next": {
            "discussions_group_at_subsection": bool,
        }
    }

The ``edx-next`` key here represents the provider id, allowing for potentially
multiple provider configs to coexist in case of switching providers etc.
Settings outside this key are those that are applicable to all providers. Note
that they may not be supported by all providers though, in which case they will
simply be ignored.

To store Unit-level discussions settings, we can simply add a boolean field
to the Unit block that specifies whether it is discussable or not. To be
consistent with the above names we can call this field ``discussions_enabled``.

A signal can be created using the new Hooks extension system proposed in OEP-50
that is triggered when discussions settings change. This signal can encapsulate
all the data needed for setting up discussions from the modulestore. It can
traverse through all teh Units in the course that match the criterion from the
discussions settings and provide the needed details as part of the signal data.

A handler for the above signal, we create the discussion topics in
``cs_comments_service`` and add a mapping. If an existing unit with discussions
is removed, we will disable the link but not delete the data.

The discussion grouping at subsections will simply combine the topics from all
the units in the subsection and provide a unified view across the subsection.
This setting will mainly be ignored and will likely only be used by the APIs
or potentially the frontend directly.

The mapping between discussion ids and units is also a very simple model:

.. code-block:: python

    class DiscussionTopicLink:
        course_key: CourseKey
        usage_key: UsageKey
        title: str
        group_id: int
        discussion_provider_id: str
        external_discussion_id: str
        enabled: bool

This structure is generic on purpose, to allow using this model for other
providers in the future, and for switching providers without data loss.
