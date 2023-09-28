Store more context for topics to allow more flexible handling of deletion
=========================================================================


Status
------

Proposal


Context
-------

The ``DiscussionTopicLink``model currently stores all relevant information
for topics in a course. It can handle both course-wide topics and in-context
topics. Currently when used for in-context discussions, each topic is linked
to a usage key that defines the context in which it is used.

However, the usage key itself is no longer sufficient once the content it
points to has been deleted. For instance, if a Unit is deleted, the usage
key no longer provides much meaningful information other than to indicate
that the topic was at one point existed in a course context. Likewise if a
section or subsection is deleted.

Once the unit the usage key for an in-context topic points to no longer
exists in the course, there is no way to indicate to moderators or course
authors where it belonged historically.

Requirements
------------

When course content is deleted, we need to be able to save more information
context about its original location in the course. Currently we only record
the topic name (unit name) and usage key. There are use cases for retaining
information about the subsection and section titles as well. This will be
used to display the section and subsection of the unit in a special Archived
category of topics in the discussions UI.


Decision
--------

We can add another JSON field to the ``DiscussionTopicLink`` model called
``context`` that can contain any additional context details as needed. We can
use this field to store the section and subsection names, so that this
information is available even for topics for deleted units.

When a Unit is deleted, the standard mechanism for handling discussion
configuration changes can be updated to  append the section and subsection
names to the topic name in this situation.

It's important to note that this mechanism will kick in even if a unit is
not deleted but is disabled for another reason, such as changing the grading
settings for its parent  subsection, or if custom visibility is used and the
unit is marked as not discussable. In these situations, the unit still
exists but the topic will still be updated to include the section and
subsection names.

Example of context
~~~~~~~~~~~~~~~~~~

.. code-block:: JSON

	{
		"section": "Introduction",
		"subsection": "Demo Course Overview",
		"unit": "Introduction: Video and Sequences"
	}


Alternative
___________

Alternatively, instead of making this a JSON field, we could add these
fields to the model directly as "section_name", "subsection_name", and
"unit_name". (Note: the reason for storing the unit name is that for future
potential provides the topic name might not match the unit name).

This ties the model to a course structure whereas a ``context`` field is more
generic and can be used in other future learning contexts.
