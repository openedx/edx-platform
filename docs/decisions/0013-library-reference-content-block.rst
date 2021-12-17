Referencing Content Blocks in Library V2
--------------------------------------------------

Status
=======
Pending

Context
=======
Currently, the courses are being stored in the Modulestore and we want the library content to be stored in the Blockstore.
To achieve this we need a referencing mechanism to reference the libraries to the courses. This referencing helps in replacing
v1 libraries (current content libraries stored on Modulestore) with v2 libraries (Blockstore backed) which are:

#. not dependent on edx-platform
#.simpler to maintain than modulestore
#. increases re-usability of the content

Terminology Used
^^^^^^^^^^^^^^^^
#. Blocks: Each reusable piece of content in a library. Example: problems, videos, HTML
#. Library: Collection of blocks in a course.


Decisions
=========
We want to be able to reference single and multiple specific blocks from a library (v2, as well as v1) into a course (that are stored in modulestore)
The workflow discussed for the interface for library content referencing would be:

#. Author chooses a library.
#. Author chooses a pool of blocks.
#. If multiple blocks of the same type are selected, ask for randomization
#. If no randomization, then ask for ordering


Implementation
^^^^^^^^^^^^^^
The library referencing flow would be implemented within the Studio and/or LMS processes of a single Open edX instance.
The library content would be stored and rendered outside the modulestore.

We would achieve this by introducing a unit_compositor subsystem. Like learning_sequences, the subsystem would be populated by CMS upon course publish. It would store a read-optimized form of:
* Metadata and child-block lists for all course Units, and
* Definitions of library blocks.

We would then update the LmsXBlockRuntime (called “CombinedSystem” until BD-13 is done) to use the unit_compositor as its backing store for units. When a unit is requested for a particular user, the unit_compositor would:
#. Load the unit’s child blocks from modulestore.
#. Replace each library reference block with its corresponding library block definitions, each overridden with any course-author-specified customizations, and each given a usage key that composes the library reference block's usage information with the library block’s definition key.
#. Return the list of blocks wrapped under a VerticalBlock, with the same usage key as the original unit, for the LmsXBlockRuntime to render.


Goals
=====
#. Move towards a unit composition system. This would provide long term stability.
#. Referenced content will be presented as separate blocks. This will help us take advantage of the atomicity of LMS that is currently being using in courseware (problem grade report, gradebook etc.)
#. Extendable to support structured libraries