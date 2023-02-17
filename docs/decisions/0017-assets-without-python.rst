Building static assets without Python
#####################################

Status
******

Pending

Will be moved to *Accepted* upon completion of re-implementation.

Context
*******

State of edx-platform frontends
===============================

New Open edX frontend development has largely moved to React-based micro-frontends (MFEs). However, edx-platform still has a few categories of important static frontend assets:

.. list-table::
   :header-rows: 1

   * - **Name**
     - Description
     - Example
     - Expected direction
   * - **Legacy LMS Frontends**
     - JS, SCSS, and other resources powering LMS views that have not yet been replatformed into MFEs
     - Instructor Dashboard assets
     - Replatform & DEPR
   * - **Legacy CMS Frontends**
     - JS, SCSS, and other resources powering Studio views that have not yet been replatformed into MFEs
     - Course outline editor and unit editor assets
     - Replatform & DEPR
   * - **Shared Frontend Files**
     - JS modules, SCSS partials, and other resources, usable by both Legacy LMS and CMS Frontends. This includes a few vendor libraries that have been committed to edx-platform in their entirety.
     - Legacy cookie policy banner; CodeMirror
     - Remove as part of full LMS/CMS frontend replatforming
   * - **npm-installed Assets**
     - JS modules and CSS files installed via NPM. Not committed to edx-platform.
     - React, studio-frontend, paragon
     - Uninstall as part of full LMS/CMS frontend replatforming
   * - **XModule Fragments**
     - JS and SCSS belonging to the older XModule-style XBlocks defined in edx-platform
     - ProblemBlock (aka CAPA) assets
     - Convert to pure XBlock fragments
   * - **XBlock Fragments**
     - JS and CSS belonging to the pure XBlocks defined in edx-platform
     - library_sourced_block.js
     - Keep and/or extract to pip-installed, per-XBlock repositories
   * - **pip-installed Assets**
     - Pre-compiled static assets shipped with several Python libraries that we install, including XBlocks. Not committed to edx-platform.
     - Django Admin, Swagger, Drag-And-Drop XBlock V2
     - Keep

*Note: this table excludes HTML templates. Templates are part of the frontend, but they are dynamically rendered by the Web application and therefore must be handled differently than static assets.*

So, with the exception of XBlock fragments and pip-installed assets, which are very simple for edx-platform to handle, we plan to eventually remove all edx-platform static frontend assets. However, given the number of remaining edx-platform frontends and speed at which they are currently being replatformed, estimates for completion of this process range from one to five years. Thus, in the medium term future, we feel that timeboxed improvements to how edx-platform handles static assets are worthwhile, especially when they address an acute pain point.

Current pain points
===================

Three particular issues have surfaced in Developer Experience Working Group discussions recently, each with some mitigations involving static assets:

.. list-table::
   :header-rows: 1

   * - Pain Point
     - Potential solution(s)

   * - edx-platform Docker images are too large and/or take too long to build.
     - Switch from large, legacy tooling packages (such as libsass-python and paver) to industry standard, precompiled ones (like node-sass or dart-sass). Remove unneccessary & slow calls to Django management commands.

   * - edx-platform Docker image layers seem to be rebuilt more often than they should.
     - Remove all Python dependencies from the static asset build process, such that changes to Python code or requirements do not always have to result in a static asset rebuild.

   * - In Tutor, using a local copy of edx-platform overwrites the Docker image's pre-installed node_modules and pre-built static assets, requiring developers to reinstall & rebuild in order to get a working platform.
     - Better parameterize the input and output paths edx-platform asset build, such that it may search for node_modules outside of edx-platform and generate assets outside of edx-platform.

All of these potential solutions would involve refactoring or entirely replacing parts of the current asset processing system.

WIP: Move these links
=====================

.. _paver: https://github.com/openedx/tutor/tree/open-release/olive.1/pavelib
.. _openedx-assets: https://github.com/overhangio/tutor/blob/v15.0.0/tutor/templates/build/openedx/bin/openedx-assets.

* `Finish upgrading frontend frameworks <https://github.com/openedx/edx-platform/issues/31616>`_
* `Move node_modules outside of edx-platform in Tutor's openedx image <https://github.com/openedx/wg-developer-experience/issues/150>`_
* `Move static assets outside of edx-platform in Tutor's openedx image <https://github.com/openedx/wg-developer-experience/issues/151>`_


Decision
********

We will largely reimplement edx-platform's asset processing system. We will aim to:

* Use well-known, npm-installed frontend tooling wherever possible.
* When bespoke processing is required, use standard POSIX tools like Bash.
* When Django/Python is absolutely required, contain its impact so that the rest of the system remains Python-free.
* Avoid unnecessary indirection or abstraction. For this task, extensibility is a non-goal, and simplicity is a virtue.
* Provide a clear migration path from the old system to the new one.
* Enable the future removal of as much legacy frontend tooling code as possible.

Consequences
************

The three top-level edx-platform asset processing actions are *build*, *collect*, and *watch*. The build action can be further broken down into five stages. Here is how those actions and stages will be reimplemented:


.. list-table::
   :header-rows: 1

   * - Description
     - Old implementation
     - New implementation

   * - **Build: All stages.** Compile, generate, copy, and otherwise process static assets so that they can be used by the Django webserver or collected elsewhere. For many Web applications, all static asset building would be coordinated via Webpack or another NPM-managed tool. Due to the age of edx-platform and its legacy XModule and Comprehensive Theming systems, though, there are five stages which need to be performed in a particular order.

     - ``paver update_assets --skip-collect``

       A Python-defined task that calls out to each build stage.

     - ``assets/build.sh``

       A Bash script that contains all build stages, with subcommands available for running each stage separately. Its command-line interface inspired by Tutor's ``openedx-assets`` script. The script will be runnable on any POSIX system, including macOS and Ubuntu and it will linted for common shell scripting mistakes using `shellcheck <https://www.shellcheck.net>`_.
     
   * - + **Build stage 1: Copy npm-installed assets** from node_modules to other folders in edx-platform. They are used by certain especially-old legacy LMS & CMS frontends that are not set up to work with npm directly.

     - ``paver update_assets --skip-collect``

       Implemented in Python within update_assets. There is no standalone command for it.

     - ``assets/build.sh npm``

       Pure Bash reimplementation.
 
   * - + **Build stage 2: Copy XModule framents** from the xmodule source tree over to input directories for Webpack and SCSS compilation. This is required for a hard-coded list of old XModule-style XBlocks. This is not required for new pure XBlocks, which include (or pip-install) their assets into edx-platform as ready-to-serve JS/CSS/etc fragments.

     - ``paver process_xmodule_assets``, or
       ``xmodule_assets``

       Equivalent paver task and console script, both pointing at to an application-level Python module. That module inspects attributes from legacy XModule-style XBlock classes in order to determine which static assets to copy and what to name them.

     - ``assets/build.sh xmodule``


       A Bash implementation of XModule asset copying. The aforementioned attributes will be moved from the XModule-style XBlock classes into a simple static JSON file, which the Bash script will be able to read.
       
       The initial implementation of build.sh may just point at ``xmodule_assets``.
   
   * - + **Build stage 3: Run Webpack** in order to to shim, minify, otherwise process, and bundle JS modules. This requires a call to the npm-installed ``webpack`` binary.

     - ``paver webpack``

       Python wrapper around a call to webpack. Invokes the ``./manage.py [lms|cms] print_setting`` multiple times in order to determine Django settings, adding which can add 20+ seconds to the build.

     - ``assets/build.sh webpack``

       Bash wrapper around a call to webpack. The script will accept parameters for Django settings rather than looking them up. Open edX distributions, such as Tutor, can choose how to supply the Django-setting-dervied parameters in an efficient manner.
   
   * - + **Build stage 4: Compile default SCSS** into CSS for legacy LMS/CMS frontends.

     -  ``paver compile_sass``

       Paver task that invokes ``sass.compile`` (from the libsass Python package) and ``rtlcss`` (installed by npm) for several different directories of SCSS.

       Note: libsass is pinned to a 2015 version with a non-trivial upgrade path. Installing it requires compiling a large C extension, noticably affecting Docker image build time.

     - ``assets/build.sh common``

       Bash reimplementation, calling ``node-sass`` and ``rtlcss``.
   
       The initial implementation of build.sh may use ``sassc``, a CLI provided by libsass, instead of node-sass. Then, ``sassc`` can be replaced by ``node-sass`` as part of a subsequent frontend framework upgrade effort.

   * - + **Build stage 5: Compiled themes' SCSS** into CSS for legacy LMS/CMS frontends. The default SCSS is used as a base, and theme-provided SCSS files are used as overrides. Themes are searched for from some number of operator-specified theme directories.

     - ``./manage.py [lms|cms] compile_sass``, or
       ``paver compile_sass --theme-dirs ...``

       The management command is a wrapper around the paver task. The former looks up the list of theme search directories from Django settings and site configuration; the latter requires them to be supplied as arguments.

       TODO

     - ``./manage.py [lms|cms] compile_sass``
       ``assets/build.sh themes --theme-dirs ...``

       The management command will remain available, but it will need to be updated to point at the Bash script, which will replace the paver task (see build stage 4 for details).

       The overall asset *build* action will use the Bash script; this means that list of theme directories will need to be provided as arguments, but it ensures that the build can remain Python-free.
   
   * - **Collect** the built static assets from edx-platform to another location (the ``STATIC_ROOT``) so that they can be efficiently served *without* Django's webserver. This step, by nature, requires Python and Django in order to find and organize the assets, which may come from edx-platform itself or from its many installed Python and NPM packages. This is only needed for **production** environments, where it is usually desirable to serve assets with something efficient like NGINX.

     - ``paver update_assets``

       Paver task wrapping a call to the standard Django `collectstatic <https://docs.djangoproject.com/en/4.1/ref/contrib/staticfiles/#collectstati>`_ command. It adds ``--noinput`` and a list of ``--ignore`` file patterns to the command call.

     - ``./manage.py lms collectstatic --noinput && ./manage.py cms collectstatic --noinput``

       The standard Django interface will be used without a wrapper. The ignore patterns will be added to edx-platform's `staticfiles app configuration <https://docs.djangoproject.com/en/4.1/ref/contrib/staticfiles/#customizing-the-ignored-pattern-list>`_ so that they do not need to be supplied as part of the command.
   
   * - **Watch** static assets for changes in the background. When a change occurs, rebuild them automatically, so that the Django webserver picks up the changes. This is only necessary in **development** environments. A few different sets of assets may be watched: XModule fragments, Webpack assets, default SCSS, and theme SCSS.

     - ``paver watch_assets``

       Paver task that invokes ``webpack --watch`` for Webpack assets and watchdog (a Python library) for other assets.

     - ``assets/build.sh --watch <stage>``

       where ``<stage>`` if one of the build stages described above

       Bash wrapprers around invocation(s) of `watchman <https://facebook.github.io/watchman/>`_, a popular file-watching library maintained by Meta. Watchman is already installed into edx-platform (and other services) via the pywatchman pip wrapper package.

       Note: This adds a Python dependency to build.sh. However, we could be clear that watchman is an *optional* dependency of build.sh, enabling the optional ``--watch`` feature. This would keep the *build* action Python-free. Alternatively, watchman is also availble Python-free via apt and homebrew.

Notes on Tutor
==============

TODO

Deprecation of the old asset processing system
==============================================

TODO

Alternatives Considered
***********************

TODO

...

