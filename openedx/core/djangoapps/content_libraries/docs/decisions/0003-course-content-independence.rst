3. Course Content should not depend on Library Content
######################################################

Status
******

Accepted


Context
*******

When a course uses content from a library via a ``LibraryContentBlock``, it creates a course-local copy of the library's blocks. For each library block, it will also store certain metadata in the ModuleStore that connects the course copy with the original in the library, such as the usage key and version of the original, as well as the library-suggested values for various fields (e.g. ``num_attempts=10``).

This metadata is not currently a part of the course export, and must be reconstructed by querying the library during the course import process. This causes a number of issues:

#. The course might be imported into a site where the library does not exist, meaning that there's no way for us to figure out what the library-suggested values should be. This becomes a problem for any block which does not override its library-suggested value: the block will fall back to the block-type-suggested value, which is often not appropriate.
#. The course might be imported into a site where a copy of the library exists, but the versions do not match. In this case, we currently just grab the latest library version metadata because we don't have anything else to go on.
#. Studio Clipboard Copy & Paste functionality depends on serialization to OLX, so this metadata information is lost when an author tries to make copies of the content in other places.

We have experienced a number of `serious bugs <https://openedx.atlassian.net/wiki/spaces/COMM/pages/3858661405/Bugs+from+Content+Libraries+V1#Issues-with-update_children>`_ because of this auto-sync behavior.

Decision
********

Content that is stored in a Course should only have to query content in a Library in the following unavoidable circumstances:

#. Initially picking the content that will be used (copied into) the Course.
#. Checking to see if an updated version of the content is available.
#. Updating the content copied into the Course with a more recent version stored in the Library (only done when a course author explicitly triggers it).

In all other cases, the course copy of the content should be self-sufficient and should not require "syncing" to a library to fill in missing metadata. In particular, the following operations should be possible to do without querying the library:

* Import and Export of courses within and across sites.
* Copy/Paste/Duplicate of content within and across courses.

Consequences
************

Technical:

* We will need to serialize more metadata into the course export, probably by adding new fields to OLX. We will need to make this metadata available for library content operations in the XBlock runtime (ADRs to follow).
* We will need to update Import/Copy-Paste/Duplicate to use this metadata rather triggering a library sync.

User-facing:

* This should remove a major source of bugs and confusion during the import process.
* We should be able to begin preserving edits to library content during the Duplicate and Copy-Paste operations, which has been impossible as long as those operations have involved a library sync.
