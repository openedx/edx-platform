Referencing Content Blocks in Library V2
--------------------------------------------------

Status
=======
Pending

Context
=======
Currently, courses are being stored in Modulestore (MongoDB) and content libraries
are stored in both Modulestore (libraries v1) and the Blockstore (libraries v2).
Until such a time as everything is moved to blockstore, the platform needs a content
reuse mechanism that allows authors to incorporate content (XBlocks) from blockstore-based
content libraries (libraries v2) into courses, and that mechanism should be reference-based
instead of needing to copy content from Blockstore into Modulestore.

There is work going on to build out the functionality of libraries v2 and migrate all
usage of content libraries to Blockstore/v2. The benefits of using the blockstore-backed
v2 content libraries are:

#. Blockstore has been designed to support use cases like content libraries and is
   easier for developers to work with compared to Modulestore, which is not really
   designed for content libraries.
#. Blockstore-backed v2 content libraries support any XBlock type, while Modulestore
   (libraries v1) only supports a few types
#. Blockstore-backed v2 content libraries can store large asset files (like images,
   videos, and PDFs) required by each XBlock, and each file is only stored once no
   matter how many times it is used.

Terminology Used
^^^^^^^^^^^^^^^^
#. Blocks: Each reusable piece of content in a library. Example: problems, videos,
   HTML. Also known as Xblocks.
#. Library: Collection of blocks that can be used in one or more courses


Decisions
=========
As of now, blockstore-backed content libraries (libraries v2) store XBlock data in
blockstore and when the library is used in a course, the blocks are copied from Blockstore
to Modulestore with the help of LibrarySourcedBlock.

The copying of blocks from Blockstore to Modulestore occupies a lot of space and Modulestore
has a lot of complexity which causes performance issues. The complete elimination of
Modulestore doesn't seem to be a pragmatic solution since it is required for backward
compatibility of courses, and significant development is required before blockstore-based
courses could achieve feature parity. So the pragmatic solution for content reuse today
is to allow reusing blockstore content in Modulestore courses more efficiently.

Hence, instead of storing blocks, the Modulestore will now store a reference to blocks
from blockstore-backed v2 content libraries. The LMS will use unit_compositor which
helps to replace each reference with its corresponding library block definitions and
apply the required course-author-specified customizations before displaying the content
to learners.

Studio will provide authors with two separate workflows, once for selecting one or
more specific blocks and adding those specific blocks to the course, and another workflow
for selecting a randomized set of blocks, so that each student will see a random block
out of the set selected by the author.

Current Architecture/Implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Currently, courses are stored in Modulestore and libraries can either be stored in
Modulestore or Blockstore. The [library_sourced_block](https://github.com/openedx/edx-platform/blob/master/xmodule/library_sourced_block.py)
is used to make a copy of blockstore-based v2 content library block and store it in
Modulestore itself as the child.


Proposed Implementation
^^^^^^^^^^^^^^
The library referencing flow would be implemented within the Studio and/or LMS. The
library content would be stored and rendered outside the Modulestore.

This is achieved by a unit_compositor subsystem. Like learning_sequences, the subsystem
would be populated by CMS upon course publish. It would store a read-optimized form of:

* Metadata and child-block lists for all course Units, and
* Definitions of library blocks.

The LmsXBlockRuntime (called “CombinedSystem” until BD-13 is done) will be updated to use
the unit_compositor as its backing store for units. When a unit is requested for a
particular user, [the unit_compositor would](https://openedx.atlassian.net/wiki/spaces/COMM/pages/3173220481/BD-14+Library+use+cases+implementation+discovery#Example%3A):

#. Load the unit’s child blocks from Modulestore.
#. Replace each library reference block with its corresponding library block definitions,
   each overridden with any course-author-specified customizations, and each given a
   usage key that composes the library reference block's usage information with the
   library block’s definition key.
#. Return the list of blocks wrapped under a VerticalBlock, with the same usage key
   as the original unit, for the LmsXBlockRuntime to render.


Goals
=====
#. Move towards a unit composition system. This would provide long-term stability.
#. Referenced content will be presented as separate blocks. This will help us take
   advantage of the atomicity of LMS that is currently being used in courseware
   (problem grade report, gradebook etc.)
#. Extendable to support structural libraries i.e the libraries with units, sequences,
   and chapters just like how courses are structured right now.
