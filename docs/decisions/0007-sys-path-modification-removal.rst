TL;DR: How to fix your code
===========================

It used to be acceptable to import code from "lms.djangoapps.something" with `import something`.  Now it must be imported with `import lms.djangoapps.something` or `from lms.djangoapps import something`.  Similar changes must be made anywhere a module is referenced.

Soon the old import style will stop working.

Status
======

In Progress

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

5. Once all instances of the ``sys.path``-based imports have been migrated in the ``edx-platform`` codebase, officially deprecate that import pattern for the next open-source release (as per the standard deprecation process).

6. Monitor logs to address continued use of the ``sys.path`` based import patterns.

Goals
=====

Eliminate modifications to ``sys.path`` to enable easier tool use in edx-platform.
