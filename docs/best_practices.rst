#######################################
edx-platform Development Best Practices
#######################################

There are many general best practices documented for `Open edX Development in
Confluence`_. The following best-practices are specific to edx-platform.

Course Access in LMS
********************

the following technologies can be used to access course-related data:

* `Course Overviews`_:  Provide performant access to course metadata.

* `Course Blocks`_: Provide performant access to the blocks in a course,
  including filtering and access control capabilities.

* `Modulestore`_ - Contains all course related data, including course metadata
  course blocks, and student module data. Course Overviews and Course Blocks are
  cached performant versions of a subset of this source data.

When coding in the LMS, it is generally preferred to use `Course Overviews`_ and
`Course Blocks`_, due to the following benefits:

1. Cached versions of course data that are better optimized for Learners.

2. A start of the separation of LMS and Studio data to move us closer to the
   ultimate ability to separate the two.

**Note**: At this time, these preferred methods are for coding in the LMS, but
   outside of the courseware.  Inside the courseware, there is more work to be
   done to take advantage of these techniques.

Prefer using `Course Overviews`_ where possible when you just need course
metadata, rather than loading the full course. For example, this could be done
by calling ``get_course_overview_with_access()`` in place of
``get_course_with_access``. If the course overview doesn't contain the data you
need, you should consider whether it makes sense to expand what is available via
the course overview. See an `example use of course overviews`_ in the course
outline feature.

Prefer using `Course Blocks`_ over loading a full course directly from the
`modulestore`_. The following is an `example of using course blocks`_ in the
course outline feature.

If you need to load student user data to combine with the data you retrieve from
the `Course Blocks`_, you can load the student module data from the modulestore
without loading the full course. Here is an `example loading the student module
data`_ in the course outline feature.

.. _Open edX Development in Confluence: https://openedx.atlassian.net/wiki/spaces/OpenDev/overview
.. _Course Overviews: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/content/course_overviews/__init__.py
.. _example use of course overviews: https://github.com/edx/edx-platform/blob/f81c21902eb0e8d026612b052557142ce1527153/openedx/features/course_experience/views/course_outline.py#L26
.. _Course Blocks: https://openedx.atlassian.net/wiki/display/EDUCATOR/Course+Blocks
.. _modulestore: https://edx.readthedocs.io/projects/edx-developer-guide/en/latest/modulestores/index.html
.. _example of using course blocks: https://github.com/edx/edx-platform/blob/f81c21902eb0e8d026612b052557142ce1527153/openedx/features/course_experience/utils.py#L65-L72
.. _example loading the student module data: https://github.com/edx/edx-platform/blob/f81c21902eb0e8d026612b052557142ce1527153/openedx/features/course_experience/utils.py#L49
