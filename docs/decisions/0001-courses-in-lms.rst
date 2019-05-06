Courses in LMS
--------------

Status
======

Accepted

Context
=======

**Note:** Within the context of the LMS, "Course" means "Course Runs", as defined in the `edX DDD Ubiquitous Language`_.

In the LMS, the following technologies can be used to access course content and metadata:

* `Course Overviews`_:  Provides performant access to course metadata.

* `Course Blocks`_: Provides performant access to the blocks in a course, including filtering and access control capabilities.

* `Modulestore`_ - Contains all course related data, including course metadata, course blocks, and student module data. `Course Overviews`_ and `Course Blocks`_ are performant read-optimized versions of subsets of data in the Modulestore.

.. _edX DDD Ubiquitous Language: https://openedx.atlassian.net/wiki/spaces/AC/pages/188032048/edX+DDD+Ubiquitous+Language
.. _Course Overviews: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/content/course_overviews/__init__.py
.. _Course Blocks: https://openedx.atlassian.net/wiki/display/EDUCATOR/Course+Blocks
.. _Modulestore: https://edx.readthedocs.io/projects/edx-developer-guide/en/latest/modulestores/index.html

Decisions
=========

When coding in the LMS, prefer to use `Course Overviews`_ and `Course Blocks`_, rather than the `Modulestore`_, for the following reasons:

1. `Course Overviews`_ and `Course Blocks`_ are optimized for read-access for Learners.

2. We eventually want to separate the LMS from Studio. Studio can have its own read-write storage layer (currently `Modulestore`_).

Course Overviews
~~~~~~~~~~~~~~~~

Use `Course Overviews`_ when you just need course metadata and not the course context. For example, call ``get_course_overview_with_access()`` in place of ``get_course_with_access``. If `Course Overviews`_ doesn't contain the data you need, expand its model or create a new joint table (if the newly desired data is conceptually different from what's in `Course Overviews`_). 

**Example:** See `example use of course overviews`_ in the course outline feature.

Course Blocks
~~~~~~~~~~~~~

Use `Course Blocks`_ instead of loading a full course directly from the `modulestore`_.

**Example:** See `example of using course blocks`_ in the course outline feature.

User's Course State
~~~~~~~~~~~~~~~~~~~

If you need to combine user data with `Course Blocks`_ data, load the users's data directly from the Courseware Student Module instead of loading the course from the `Modulestore`_.

**Example**: See `example loading the student module data`_ in the course outline feature.

.. _example use of course overviews: https://github.com/edx/edx-platform/blob/f81c21902eb0e8d026612b052557142ce1527153/openedx/features/course_experience/views/course_outline.py#L26
.. _example of using course blocks: https://github.com/edx/edx-platform/blob/f81c21902eb0e8d026612b052557142ce1527153/openedx/features/course_experience/utils.py#L65-L72
.. _example loading the student module data: https://github.com/edx/edx-platform/blob/f81c21902eb0e8d026612b052557142ce1527153/openedx/features/course_experience/utils.py#L49

Tech Debt
=========

At this time, `LMS courseware rendering`_ still uses the `Modulestore`_ instead of `Course Blocks`_. This is technical debt that needs to be addressed, so we can have a fuller separation between the storage systems.

.. _LMS courseware rendering: https://github.com/edx/edx-platform/blob/67008cec68806b77631e8c40ede98ace8a83ce4f/lms/djangoapps/courseware/module_render.py#L291

Consequences
============

* LMS-specific course content storage will evolve separately from Studio's storage, allowing for decoupled optimizations.

* LMS views will perform better when using storage that is read-optimized.
