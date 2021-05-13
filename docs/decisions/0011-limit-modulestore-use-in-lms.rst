Limit LMS Modulestore access to the courseware app
--------------------------------------------------

Context
=======

Django apps deployed in the LMS sometimes want to make queries about course team authored content, like sequences, units, and problems. To do this, they often use the Modulestore, which can return parts of the course as a graph of XBlocks. Unfortunately, the Modulestore is a large, complex system that is shared by many features. This has been the cause of many bugs and performance issues over the years. Modulestore performance has been gradually improved over the years, but at the cost of adding even more complexity.

The courseware app is the exception to this rule, because it requires Modulestore access to render the Unit with the XBlock runtime, and extracting that logic would require too much effort at this time.

Decisions
=========

#. New features will be implemented without making calls to the Modulestore in the LMS.
#. Teams should opportunistically remove LMS Modulestore dependencies in existing features as they are being worked on.
#. Apps may still access the Modulestore from the Studio rpro.
#. Apps should make use of newer, more limited LMS APIs that can answer some of the same questions. This includes CourseOverviews for settings metadata and Learning Sequences for course outlines.
#. Apps that need other course content data should push that data into their own data models during course publish, by listening to the course_published signal and launching a celery task that will query the Modulestore in the Studio process.

Goals
=====

**Application correctness is easier to reason about.**
  Modulestore often has obscure edge cases like non-standard course hierarchies, inheritable attributes set in places where Studio would not normally offer it as an option, A/B tests at the section level, etc. However, LMS-oriented relational data schemas like ``course_overviews`` and ``learning_sequences`` make intentional, documented assumptions about course data. LMS app authors can confidently build on these simpler models without having to mind the complex flexibility of Modulestore data.

**Application behavior is more predictable.**
  Modulestore grabs large chunks of the course at once, leading to major variability in performance in small vs. large courses, or in courses where certain advanced features have been enabled. Serving LMS requests from simpler application data models will make the operational behavior much more predictable. The eventual goal would be to access Modulestore only during the authoring and publishing steps, and never when serving content to students.

**Tests are easier to write and run faster.**
  CourseOverviews and UserCourseOutlineData objects are much easier to create and mock for testing purposes than a tree of XBlocks, and do not suffer from complicated publishing rules. Using the modulestore also imposes a substantial performance penalty when creating and modifying courses, making modulestore access the dominant part of the edx-platform test suite running time.

**Applications are more resilient to user-facing failures.**
  Many features today are at least partially implemented in Modulestore and the XBlocks that it returns. Changes in those features can cause bugs that ripple out into completely unrelated features being developed by other teams.

  If an LMS application queries the Modulestore when responding to a user request, then unexpected failures in shared Modulestore code will cause user-facing errors. A feature that reads Modulestore data at the time of course publish and pushes it into its own data model will still be affected by Modulestore-related bugs, but it will result in stale data and not an entirely broken experience.

**We can reduce the size of the edx-platform monolith.**
  It is possible that smaller apps like ``course_overviews`` and ``learning_sequences`` could be extracted from edx-platform and become their own app repositories. When that happens, an app that lives in its own repository could include those smaller apps as dependencies, simplifying the setup and running of tests. Modulestore has proven to be much more challenging to extract in this way, and any external apps relying on the modulestore will be forced to use dependency inversion mechanisms that are more vulnerable to breaking as edx-platform evolves. This will also advance our long term plans for separating Studio and the LMS into more separate systems.


Conversion Guide
=================

There are a couple of performant alternatives to the Modulestore for common use cases. If neither of these alternatives satisfies your use case, please see the "Advanced Use Cases" section.

Course Settings
***************

Apps that only query the Modulestore for course settings that are stored on the root CourseBlock should be modified to query CourseOverviews instead. This is available from ``openedx.core.djangoapps.content.course_overview.api``, which has the ``get_course_overview`` and ``get_course_overviews`` functions.

If the settings data is not currently captured in the CourseOverview model, do the following:

#. Add the fields to the CourseOverview model, with default values.
#. Generate the migration file.
#. Increment CourseOverview.VERSION by one.
#. Update CourseOverview._create_or_update to properly load the data from the CourseBlock object (from modulestore) and into the CourseOverview class. Attributes are typically named the same on both classes.

This will cause a performance penalty on initial rollout. The CourseOverviews API will make sure that you don't get an old version of the data, and will force just-in-time re-generation of the overview if the stored record version is less than CourseOverview.VERSION. This should resolve a few minutes after deployment.

Course Outline / Sequence Metadata
**********************************

Apps that need course outline data and metadata about sequences can make use of the Learning Sequences public API from the ``openedx.core.djangoapps.content.learning_sequences.api`` package. A couple of important caveats to the functions advertised here:

* Old Mongo courses are not supported. These are soon-to-be-removed courses with course keys of the format "Org/Course/Run". All course keys that begin with "course-v1:" or "ccx-v1:" are supported.
* This is a new API, and new API functions and data will be added over time.

Advanced Use Cases
******************

Sometimes the data an application needs just isn't available in a performant way in the LMS. When this happens, you'll need to create your own model for this data in your application, and then push new data to it during the course publish process. To demonstrate how this can work, let's walk through the implementation of Learning Sequences, which follows this general architectural pattern.


Studio Process
^^^^^^^^^^^^^^

The code to extract data from the Modulestore and convert it into a format that the Learning Sequences app understands lives in the ``cms.djangoapps.contentstore`` package. This has several pieces:

Data Extraction
  ``cms.djangoapps.contentstore.outlines.get_outline_from_modulestore``

  The ``get_outline_from_modulestore`` function and its helpers does the work of actually extracting course structure and content data from the Modulestore. It's where we have to account for any weird edge cases, like malformed course structures.

  Note that this function has no side-effects. To make testing easier, it's purely about extracting content and converting it to the ``CourseOutlineData`` objects that Learning Sequences understands. The test cases in ``OutlineFromModuleStoreTestCase`` then only have to worry about setting up Modulestore course structures and validating that they generate the expected ``CourseOutlineData``.

  You'll also want to be careful to make sure you're only pulling from the published branch when you extract this data (saving a draft also generates a ``course_published`` event). You can force a read from the publish branch by
  writing something like::

    from xmodule.modulestore import ModuleStoreEnum
    from xmodule.modulestore.django import modulestore

    # ...

    store = modulestore()
    with store.branch_setting(ModuleStoreEnum.Branch.published_only, course_key):
        course = store.get_course(course_key, depth=3)

  Finally, keep in mind that your code will run asynchronously after the the user has pressed the publish button or run course import. That means that you should be forgiving of the input to a certain degree, and not simply fail the process because you encounter bad course data. On the other hand, it's important to keep this part of the code as a strong anti-corruption layer. We don't want to let unnecessary complexity and obscure data configurations leak into our application's core data model.

  The compromise that Learning Sequences takes is to elevate content errors to a first-class concept. The Modulestore data extraction code returns not only the ``CourseOutlineData``, but a list of ``ContentErrorData`` objects as well.

  For example, Learning Sequences assumes that a Sequence exists in only one Section in the Course. This simplifying assumption is baked into the data model and URLs structure of the ``learning_sequences`` app, but it's not a constraint that Modulestore imposes on courses. So our approach should be to create a ``ContentErrorData`` whenever we see this happen, and skip over all but the first occurance of the Sequence. The data model for Learning Sequences remains simple, and there is some representation of what went wrong that could be used by course teams or support staff to diagnose any problems later.

  In summary: Strict/Simple data model for your App, Forgiving transformation of data from Modulestore.

Writing to our App Models
  ``cms.djangoapps.contentstore.outlines.update_outline_from_modulestore``

  The ``update_outline_from_modulestore`` is a short function that calls ``get_outline_from_modulestore`` to create a representation of the data that the ``learning_sequences`` app understands (``CourseOutlineData``), and then pushes that data into ``learning_sequences`` via an API method that ``learning_sequences`` exposes (``replace_course_outline``).

  This function also sets custom attributes so that we can better monitor for performance issues and errors.

  Note: One of the things we write is the *version* of the course. This is going to be important for diagnosing what's going on if these writes ever start failing. We get this information from the ``course_version`` attribute on the root ``CourseBlock``, and convert that to a string for convenient storage (it's a BSON object).

Celery Task
  ``cms.djangoapps.contentstore.outlines.tasks.update_outline_from_modulestore_task``

  This is a simple celery ``@shared_task`` that wraps the call to``update_outline_from_modulestore``. It's critical to use celery to do this work asynchronously. Even if your code seems to work quickly enough to run in-process, courses can often use obscure features that can drastically increase the time it takes to get data out, and you will almost certainly not be able to comprehensively test for all those situations.

  *You must be aggressive about alerting on task failures*. Publishes are infrequent enough to make it so that certain content-dependent errors will not trigger most error rate alerts. You have to be extremely sensitive to outright failures in your task because you may be blocking the publish for a course.

Signal Handler
  ``cms.djangoapps.contentstore.outlines.signals.handlers.listen_for_course_publish``

  This is a centralized location where Studio does its post-publish data pushes, but you can also make a separate handler that listens for the same ``course_published`` signal. Its main task is to do some logging and queue the celery task.

Management Task
  ``cms.djangoapps.contentstore.management.commands.backfill_course_outlines``
  ``cms.djangoapps.contentstore.management.commands.update_course_outline``

  Management commands to backfill a group of course outlines or to update one particular command. A few things to note:

  #. These commands live in the Studio process, because they are invoking code that will query the Modulestore.
  #. The backfill command launches a new celery task for every individual course. This is both to control memory usage (successive Modulestore access across courses will leak a lot of memory), as well as to make it easier to see which courses are taking longer and/or causing errors.
  #. In the long term, you will want a way to trigger backfills from the Django admin, so that you don't need to file a support ticket every time.

LMS Process
^^^^^^^^^^^

In the LMS process, your feature should not use the Modulestore at all. Your LMS app's code should be entirely free of Modulestore dependencies. All of the Modulestore-facing code described above should live in the ``./cms/`` source tree and run in the Studio process. By the time your LMS request is happening, your app is only looking at its own data models, or one of the performant Modulestore-alternative APIs.

You should not allow the LMS process to overwrite models written to by the course publishing process, and you should absolutely not let the LMS push data back into the Modulestore. If your application needs to be able to override data that comes from publishing, have two separate models–one that's only ever updated by course content publishing, and one that's read/write from the LMS. When answering queries, your app can look at both models. The edx-when app works in this way, capturing start and due date information from the Modulestore, but then applying student-specific overrides when serving requests in the LMS. For more background on this topic, please see `ADR 5: LMS Subdomain Boundaries <./docs/decisions/0005-studio-lms-subdomain-boundaries.rst>`_ .


Django Admin
^^^^^^^^^^^^

The Django admin for the ``learning_sequences`` app is read-only, and is intended to give support and engineering an easier view into the state of what's on production. We are planning to add the backfill task as an action to a new Django admin page in the contentstore Studio app, using a proxy model to CourseOverview in order to get the listing of courses.
