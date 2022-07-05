TL;DR: How to fix your code
===========================

It used to be acceptable to import code from "lms.djangoapps.something" with `import something`.  Now it must be imported with `import lms.djangoapps.something` or `from lms.djangoapps import something`.  Similar changes must be made anywhere a module is referenced.

Soon the old import style will stop working.


Status
======

Complete (as of the Lilac Open edX release)


Context
=======

Early in the life of edx-platform, code was added to the django settings to put certain libraries direcly into the python ``sys.path``, to facilitate imports and future removal of those libraries into their own python installation packages. Those future goals of moving the packages out of the main repository were never realized, but the changes to ``sys.path`` have remained in the codebase.

Unfortunately, runtime modifications to ``sys.path`` make it difficult for many common python tools to analyze the codebase without additional configuration. (For instance, ``pylint`` needs to be configured to search for imports in the same paths that are added to ``sys.path`` in the django settings.) Additionally, as we've made the paths importable directly, there are now two ways to imports some packages (for instance, ``import lms.djangoapps.courseware`` and ``import courseware``). However, importing the same module twice but with different names actually triggers the module-level code to be executed multiple times, which can cause some unexpected runtimes errors.

Decision
========

In order to simplify the edx-platform code environment, we will remove the modifications to ``sys.path``, with a period of deprecation to allow third-party libraries that might be relying on the ``sys.path``-based import names to continue to function while logging warnings.

This deprecation will take place in the following steps:

1. Add a new folder (``import_shims``) to isolate the code used for deprecation warnings.

2. For every module importable using the ``sys.path`` style (for instance, ``courseware``), duplicate that module structure into the ``import_shims/lms`` (or ``import_shims/studio``) directory. Each file in that directory should do a wild-card import of the corresponding ``lms.djangoapps.`` module, and should log a warning indicating where it was imported from. For example, in ``import_shims/lms/courseware/views/views.py``, it will wild-card import ``from lms.djangoapps.courseware.views.views import *``. The ``import_shims/generate_shims.sh`` script will generate these files.

3. The ``sys.path`` modification will be changed to point to ``import_shims/lms``, rather than ``lms/djangoapps``. At this point, any code that references the modules directly will trigger warnings with logging about where the imports were coming from (to drive future cleanup efforts). The warnings will be instances of ``DeprecatedEdxPlatformImportWarning`` (subclass of ``DeprecationWarning``).

4. Fix all instances where the ``sys.path``-based modules were ``patch``-ed in unit tests, as those patches no longer work.

5. Once all instances of the ``sys.path``-based imports have been migrated in the ``edx-platform`` codebase, officially deprecate that import pattern for the next open-source release.

6. Monitor logs to address continued use of the ``sys.path`` based import patterns.

Goals
=====

Eliminate modifications to ``sys.path`` to enable easier tool use in edx-platform.


Timeline
========

In the Koa release, usages of the old import style raised instances of
``DeprecatedEdxPlatformImportWarning``, but still worked.

In the Lilac release, usages of old import paths will raise instances of
``DeprecatedEdxPlatformImportError``, breaking any code that was not updated.
This error class is intentionally *not* a subclass of ``ImportError``;
to understand why, consider the following common pattern used in packages outside
of the edx-platform repo itself::
  try:
      from student.models import CourseEnrollment
  except ImportError:
      CourseEnrollment = None
This pattern is (unfortunately) widely used to so packages can import
objects from edx-platform modules in developer or production environments,
whilst falling back to ``None`` when unit tests are run.
Now, if the the above old-style import statement raised a subclass of
``ImportError``, then it would be silently caught by the ``except`` clause!
By instead raising from a disjoint error class in the Lilac release,
we make it more likely that operators can quickly notice and fix
any lingering old-style import paths as they migrate from Koa.

In Maple and beyond, old import paths will simply raise ``ImportError``,
allowing us to remove the ``import_shims`` directory tree.


Upgrade Guide
=============

Where to look for old import paths:

* Forks of ``edx-platform`` itself.
* Packages that import edx-platform code (``edx-completion``, ``edx-enterprise``, et al).
* Repositories/files that override Ansible variables or ``edx-platform`` Django settings.

What forms old import paths may take:

* Direct imports (e.g. ``import courseware.views``)
* Direct "from" imports (e.g. ``from contentstore.models import VideoUploadConfig``)
* String references to modules (e.g. ``@patch('edxmako.LOOKUP', {})``)
* YAML references to modules (e.g. ``KEY_FUNCTION: util.memcache.safe_key``)

What the old imports are, and their replacements:

+-------------------------------+----------------------------------------------+
+ **Old prefix**                | **New prefix**                               |
+-------------------------------+----------------------------------------------+
| ``badges``                    | ``lms.djangoapps.badges``                    |
+-------------------------------+----------------------------------------------+
| ``branding``                  | ``lms.djangoapps.branding``                  |
+-------------------------------+----------------------------------------------+
| ``bulk_email``                | ``lms.djangoapps.bulk_email``                |
+-------------------------------+----------------------------------------------+
| ``bulk_enroll``               | ``lms.djangoapps.bulk_enroll``               |
+-------------------------------+----------------------------------------------+
| ``ccx``                       | ``lms.djangoapps.ccx``                       |
+-------------------------------+----------------------------------------------+
| ``certificates``              | ``lms.djangoapps.certificates``              |
+-------------------------------+----------------------------------------------+
| ``commerce``                  | ``lms.djangoapps.commerce``                  |
+-------------------------------+----------------------------------------------+
| ``course_api``                | ``lms.djangoapps.course_api``                |
+-------------------------------+----------------------------------------------+
| ``course_blocks``             | ``lms.djangoapps.course_blocks``             |
+-------------------------------+----------------------------------------------+
| ``course_goals``              | ``lms.djangoapps.course_goals``              |
+-------------------------------+----------------------------------------------+
| ``course_home_api``           | ``lms.djangoapps.course_home_api``           |
+-------------------------------+----------------------------------------------+
| ``courseware``                | ``lms.djangoapps.courseware``                |
+-------------------------------+----------------------------------------------+
| ``coursewarehistoryextended`` | ``lms.djangoapps.coursewarehistoryextended`` |
+-------------------------------+----------------------------------------------+
| ``course_wiki``               | ``lms.djangoapps.course_wiki``               |
+-------------------------------+----------------------------------------------+
| ``debug``                     | ``lms.djangoapps.debug``                     |
+-------------------------------+----------------------------------------------+
| ``discussion``                | ``lms.djangoapps.discussion``                |
+-------------------------------+----------------------------------------------+
| ``edxnotes``                  | ``lms.djangoapps.edxnotes``                  |
+-------------------------------+----------------------------------------------+
| ``experiments``               | ``lms.djangoapps.experiments``               |
+-------------------------------+----------------------------------------------+
| ``gating``                    | ``lms.djangoapps.gating``                    |
+-------------------------------+----------------------------------------------+
| ``grades``                    | ``lms.djangoapps.grades``                    |
+-------------------------------+----------------------------------------------+
| ``instructor``                | ``lms.djangoapps.instructor``                |
+-------------------------------+----------------------------------------------+
| ``instructor_analytics``      | ``lms.djangoapps.instructor_analytics``      |
+-------------------------------+----------------------------------------------+
| ``instructor_task``           | ``lms.djangoapps.instructor_task``           |
+-------------------------------+----------------------------------------------+
| ``learner_dashboard``         | ``lms.djangoapps.learner_dashboard``         |
+-------------------------------+----------------------------------------------+
| ``lms_initialization``        | ``lms.djangoapps.lms_initialization``        |
+-------------------------------+----------------------------------------------+
| ``lms_xblock``                | ``lms.djangoapps.lms_xblock``                |
+-------------------------------+----------------------------------------------+
| ``lti_provider``              | ``lms.djangoapps.lti_provider``              |
+-------------------------------+----------------------------------------------+
| ``mailing``                   | ``lms.djangoapps.mailing``                   |
+-------------------------------+----------------------------------------------+
| ``mobile_api``                | ``lms.djangoapps.mobile_api``                |
+-------------------------------+----------------------------------------------+
| ``monitoring``                | ``lms.djangoapps.monitoring``                |
+-------------------------------+----------------------------------------------+
| ``program_enrollments``       | ``lms.djangoapps.program_enrollments``       |
+-------------------------------+----------------------------------------------+
| ``rss_proxy``                 | ``lms.djangoapps.rss_proxy``                 |
+-------------------------------+----------------------------------------------+
| ``shoppingcart``              | ``lms.djangoapps.shoppingcart``              |
+-------------------------------+----------------------------------------------+
| ``staticbook``                | ``lms.djangoapps.staticbook``                |
+-------------------------------+----------------------------------------------+
| ``static_template_view``      | ``lms.djangoapps.static_template_view``      |
+-------------------------------+----------------------------------------------+
| ``support``                   | ``lms.djangoapps.support``                   |
+-------------------------------+----------------------------------------------+
| ``survey``                    | ``lms.djangoapps.survey``                    |
+-------------------------------+----------------------------------------------+
| ``teams``                     | ``lms.djangoapps.teams``                     |
+-------------------------------+----------------------------------------------+
| ``tests``                     | ``lms.djangoapps.tests``                     |
+-------------------------------+----------------------------------------------+
| ``verify_student``            | ``lms.djangoapps.verify_student``            |
+-------------------------------+----------------------------------------------+
| ``course_action_state``       | ``common.djangoapps.course_action_state``    |
+-------------------------------+----------------------------------------------+
| ``course_modes``              | ``common.djangoapps.course_modes``           |
+-------------------------------+----------------------------------------------+
| ``database_fixups``           | ``common.djangoapps.database_fixups``        |
+-------------------------------+----------------------------------------------+
| ``edxmako``                   | ``common.djangoapps.edxmako``                |
+-------------------------------+----------------------------------------------+
| ``entitlements``              | ``common.djangoapps.entitlements``           |
+-------------------------------+----------------------------------------------+
| ``pipeline_mako``             | ``common.djangoapps.pipeline_mako``          |
+-------------------------------+----------------------------------------------+
| ``static_replace``            | ``common.djangoapps.static_replace``         |
+-------------------------------+----------------------------------------------+
| ``status``                    | ``common.djangoapps.status``                 |
+-------------------------------+----------------------------------------------+
| ``student``                   | ``common.djangoapps.student``                |
+-------------------------------+----------------------------------------------+
| ``terrain``                   | ``common.djangoapps.terrain``                |
+-------------------------------+----------------------------------------------+
| ``third_party_auth``          | ``common.djangoapps.third_party_auth``       |
+-------------------------------+----------------------------------------------+
| ``track``                     | ``common.djangoapps.track``                  |
+-------------------------------+----------------------------------------------+
| ``util``                      | ``common.djangoapps.util``                   |
+-------------------------------+----------------------------------------------+
| ``xblock_django``             | ``common.djangoapps.xblock_django``          |
+-------------------------------+----------------------------------------------+
| ``api``                       | ``cms.djangoapps.api``                       |
+-------------------------------+----------------------------------------------+
| ``cms_user_tasks``            | ``cms.djangoapps.cms_user_tasks``            |
+-------------------------------+----------------------------------------------+
| ``contentstore``              | ``cms.djangoapps.contentstore``              |
+-------------------------------+----------------------------------------------+
| ``course_creators``           | ``cms.djangoapps.course_creators``           |
+-------------------------------+----------------------------------------------+
| ``maintenance``               | ``cms.djangoapps.maintenance``               |
+-------------------------------+----------------------------------------------+
| ``models``                    | ``cms.djangoapps.models``                    |
+-------------------------------+----------------------------------------------+
| ``pipeline_js``               | ``cms.djangoapps.pipeline_js``               |
+-------------------------------+----------------------------------------------+
| ``xblock_config``             | ``cms.djangoapps.xblock_config``             |
+-------------------------------+----------------------------------------------+
