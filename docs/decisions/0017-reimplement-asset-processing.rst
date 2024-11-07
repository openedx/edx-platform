Reimplement edx-platform static asset processing
################################################

Overview
********

* edx-platform has a complicated process for managing its static frontend assets. It slows down both developers and site operators.
* We will deprecate the current paver-based asset processing system in favor of a new implementation based primarily on frontend tools and bash.
* After one named release, the deprecated paver system will be removed.

Status
******

**Accepted**

This was `originally authored <https://github.com/openedx/edx-platform/pull/31790>`_ in March 2023. We `modified it in July 2023 <https://github.com/openedx/edx-platform/pull/32804>`_ based on learnings from the implementation process, and then `modified and it again in May 2024 <https://github.com/openedx/edx-platform/pull/34554>`_ to make the migration easier for operators to understand.

Related deprecation tickets:

* `[DEPR]: Asset processing in Paver <https://github.com/openedx/edx-platform/issues/31895>`_
* `[DEPR]: Paver <https://github.com/openedx/edx-platform/issues/34467>`_

Context
*******

State of edx-platform frontends (early 2023)
============================================

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
     - Switch from large, legacy tooling packages (such as libsass-python and paver) to industry standard, pre-compiled ones (like node-sass or dart-sass). Remove unnecessary & slow calls to Django management commands.

   * - edx-platform Docker image layers seem to be rebuilt more often than they should.
     - Remove all Python dependencies from the static asset build process, such that changes to Python code or requirements do not always have to result in a static asset rebuild.

   * - In Tutor, using a local copy of edx-platform overwrites the Docker image's pre-installed node_modules and pre-built static assets, requiring developers to reinstall & rebuild in order to get a working platform.
     - Better parameterize the input and output paths edx-platform asset build, such that it may `search for node_modules outside of edx-platform <https://github.com/openedx/wg-developer-experience/issues/150>`_ and `generate assets outside of edx-platform <https://github.com/openedx/wg-developer-experience/issues/151>`_.

All of these potential solutions would involve refactoring or entirely replacing parts of the current asset processing system.

Decision
********

We will largely reimplement edx-platform's asset processing system. We will aim to:

* Use well-known, npm-installed frontend tooling wherever possible.
* When bespoke processing is required, use standard POSIX tools like Bash.
* When Python is absolutely required, minimize the scope of its usage and the set of required Python libraries.
* Avoid unnecessary indirection or abstraction. For this task, extensibility is a non-goal, and simplicity is a virtue.
* Provide a clear migration path from the old system to the new one.
* Enable the future removal of as much legacy frontend tooling code as possible.

Consequences
************

Reimplementation Specification
==============================

Commands and stages
-------------------

**May 2024 update:** See the `static assets reference <../references/static-assets.rst>`_ for
the latest commands.

The three top-level edx-platform asset processing actions are *build*, *collect*, and *watch*. The build action can be further broken down into five stages. Here is how those actions and stages will be reimplemented:


.. list-table::
   :header-rows: 1

   * - Description
     - Old implementation
     - New implementation

   * - **Build: All stages.** Compile, generate, copy, and otherwise process static assets so that they can be used by the Django webserver or collected elsewhere. For many Web applications, all static asset building would be coordinated via Webpack or another NPM-managed tool. Due to the age of edx-platform and its legacy XModule and Comprehensive Theming systems, though, there are five stages which need to be performed in a particular order.

     - ``paver update_assets --skip-collect``

       A Python-defined task that calls out to each build stage.

     - ``npm clean-install && npm run build``

       Simple NPM wrappers around the build stages. The wrappers will be written in Bash and tested on both GNU+Linux and macOS.

       These commands are a "one stop shop" for building assets, but more efficiency-oriented users may choose to run build stages individually.

   * - + **Build stage 1: Copy npm-installed assets** from node_modules to other folders in edx-platform. They are used by certain especially-old legacy LMS & CMS frontends that are not set up to work with npm directly.

     - ``paver update_assets --skip-collect``

       Implemented in Python within update_assets. There is no standalone command for it.

     - ``npm install``

       An NPM post-install hook will automatically call scripts/copy-node-modules.sh, a pure Bash reimplementation of the node_modules asset copying, whenever ``npm install`` is invoked.

   * - + **Build stage 2: Copy XModule fragments** from the xmodule source tree over to input directories for Webpack and SCSS compilation. This is required for a hard-coded list of old XModule-style XBlocks. This is not required for new pure XBlocks, which include (or pip-install) their assets into edx-platform as ready-to-serve JS/CSS/etc fragments.

     - ``paver process_xmodule_assets``, or

       ``xmodule_assets``

       Equivalent paver task and console script, both pointing at to an application-level Python module. That module inspects attributes from legacy XModule-style XBlock classes in order to determine which static assets to copy and what to name them.

     - (step no longer needed)

       We will `remove the need for this step entirely <https://github.com/openedx/edx-platform/issues/31624>`_.

   * - + **Build stage 3: Run Webpack** in order to to shim, minify, otherwise process, and bundle JS modules. This requires a call to the npm-installed ``webpack`` binary.

     - ``paver webpack``

       Python wrapper around a call to webpack. Invokes the ``./manage.py [lms|cms] print_setting`` multiple times in order to determine Django settings, adding which can add 20+ seconds to the build.

     - ``npm run webpack``

       Simple shell script defined in package.json to invoke Webpack in prod or dev mode. The script will look for several environment variables, with a default defined for each one. See **Build Configuration** for details. The script will NOT invoke ``print_setting``; we leave to distributions the tasking of setting environment variables appropriately.

       To continue using ``print_setting``, one could run: ``STATIC_ROOT_LMS="$(./manage.py lms print_setting STATIC_ROOT_LMS)" npm run webpack``

   * - + **Build stage 4: Compile default SCSS** into CSS for legacy LMS/CMS frontends.

     - ``paver compile_sass``

       Paver task that invokes ``sass.compile`` (from the libsass Python package) and ``rtlcss`` (installed by npm) for several different directories of SCSS.

       Note: We compile SCSS using ``libsass-python==0.10.0``, a deprecated library from 2015. Installing it requires compiling a large C extension, noticeably affecting Docker image build time. The upgrade path is non-trivial and would require updating many SCSS file in edx-platform.

     - ``npm run compile-sass``

       A functionally equivalent reimplementation, wrapped as an ``npm run`` command in package.json. Due to our SCSS version, the underlying script will be written in Python, although its only Python library requirements will be ``libsass-python`` and ``click``, which will be specified in a new separate edx-platform requirements file. This will be an improvement because the script will not rely on the presence of paver, base Python requirements, or any other edx-platform Python code.

       If and when `we upgrade from libsass-python <https://github.com/openedx/edx-platform/issues/31616>`_ to a more modern tool like ``node-sass`` or ``dart-sass``, this underlying script could opaquely be rewritten in Bash, removing the Python requirement altogether.

   * - + **Build stage 5: Compile themes' SCSS** into CSS for legacy LMS/CMS frontends. The default SCSS is used as a base, and theme-provided SCSS files are used as overrides. Themes are searched for from some number of operator-specified theme directories.

     - ``./manage.py [lms|cms] compile_sass``, or

       ``paver compile_sass --theme-dirs X Y --themes A B``

       The management command is a wrapper around the paver task. The former looks up the list of theme search directories from Django settings and site configuration; the latter requires them to be supplied as arguments.

     - ``./manage.py [lms|cms] compile_sass``, or

       ``npm run compile-sass -- --theme-dir X --theme-dir Y --theme A --theme B``

       The management command will remain available, but it will be updated to point at ``npm run compile-sass``, which will replace the paver task (see build stage 4 for details).

   * - **Collect** the built static assets from edx-platform to another location (the ``STATIC_ROOT``) so that they can be efficiently served *without* Django's webserver. This step, by nature, requires Python and Django in order to find and organize the assets, which may come from edx-platform itself or from its many installed Python and NPM packages. This is only needed for **production** environments, where it is usually desirable to serve assets with something efficient like NGINX.

     - ``paver update_assets``

       Paver task wrapping a call to the standard Django `collectstatic <https://docs.djangoproject.com/en/4.1/ref/contrib/staticfiles/#collectstati>`_ command. It adds ``--noinput`` and a list of ``--ignore`` file patterns to the command call.

       (This command also builds assets. The *collect* action could not be run on its own without calling pavelib's Python interface.)

     - ``./manage.py lms collectstatic --noinput && ./manage.py cms collectstatic --noinput``

       The standard Django interface will be used without a wrapper. The ignore patterns will be added to edx-platform's `staticfiles app configuration <https://docs.djangoproject.com/en/4.1/ref/contrib/staticfiles/#customizing-the-ignored-pattern-list>`_ so that they do not need to be supplied as part of the command.

   * - **Watch** static assets for changes in the background. When a change occurs, rebuild them automatically, so that the Django webserver picks up the changes. This is only necessary in **development** environments. A few different sets of assets may be watched: XModule fragments, Webpack assets, default SCSS, and theme SCSS.

     - ``paver watch_assets``

       Paver task that invokes ``webpack --watch`` for Webpack assets and watchdog (a Python library) for other assets.

     - ``npm run watch``

       Bash wrappers around invocations of the `watchdog library <https://pypi.org/project/watchdog/>`_ for themable/themed assets, and `webpack --watch <https://webpack.js.org/configuration/watch/>`_ for Webpack-managed assets. Both of these tools are available via dependencies that are already installed into edx-platform.

       We considered using `watchman <https://facebook.github.io/watchman/>`_, a popular file-watching library maintained by Meta, but found that the Python release of the library is poorly maintained (latest release 2017) and the documentation is difficult to follow. `Django uses pywatchman but is planning to migrate off of it <https://code.djangoproject.com/ticket/34479>`_ and onto `watchfiles <https://pypi.org/project/watchfiles/>`_. We considered watchfiles, but decided against adding another developer dependency to edx-platform. Future developers could consider migrating to watchfiles if it seemed worthwile.


Build Configuration
-------------------

**May 2024 update:** See the `static assets reference <../references/static-assets.rst>`_ for
the latest configuration settings.

To facilitate a generally Python-free build reimplementation, we will require that certain Django settings now be specified as environment variables, which can be passed to the build like so::

  MY_ENV_VAR="my value" npm run build    # Set for the whole build.
  MY_ENV_VAR="my value" npm run webpack  # Set for just a single step, like webpack.

For Docker-based distributions like Tutor, these environment variables can instead be set in the Dockerfile.

Some of these options will remain as Django settings because they are used in edx-platform application code. Others will be removed, as they were only read by the asset build.

.. list-table::
   :header-rows: 1

   * - Django Setting (Before)
     - Description
     - Django Setting (After)
     - Environment Variable (After)

   * - ``WEBPACK_CONFIG_PATH``
     - Path to Webpack config file. Defaults to ``webpack.prod.config.js``.
     - *removed*
     - ``WEBPACK_CONFIG_PATH``

   * - ``STATIC_ROOT`` (LMS)
     - Path to which LMS's static assets will be collected. Defaults to ``test_root/staticfiles``.
     - ``STATIC_ROOT`` (LMS)
     - ``STATIC_ROOT_LMS``

   * - ``STATIC_ROOT`` (CMS)
     - Path to which CMS's static assets will be collected. Defaults to ``$STATIC_ROOT_CMS/studio``.
     - ``STATIC_ROOT`` (CMS)
     - ``STATIC_ROOT_CMS``

   * - ``JS_ENV_EXTRA_CONFIG``
     - Global configuration object available to edx-platform JS modules. Specified as a JSON string. Defaults to the empty object (``"{}"``). Only known use as of writing is to add configuration and plugins for the TinyMCE editor.
     - *removed*
     - ``JS_ENV_EXTRA_CONFIG``

   * - ``COMPREHENSIVE_THEME_DIRS``
     - Directories that will be searched when compiling themes.
     - ``COMPREHENSIVE_THEME_DIRS``
     - ``COMPREHENSIVE_THEME_DIRS``

Migration
=========

We will `communicate the deprecation <https://github.com/openedx/edx-platform/issues/31895>`_ of the old asset system upon provisional acceptance of this ADR.

The old and new systems will both be available for at least one named release. Operators will encouraged to try the new asset processing system and report any issues they find. The old asset system will print deprecation warnings, recommending equivalent new commands to operators. Eventually, the old asset processing system will be entirely removed.

Tutor migration guide
---------------------

Tutor provides the `openedx-assets <https://github.com/overhangio/tutor/blob/v15.3.0/tutor/templates/build/openedx/bin/openedx-assets>`_ Python script on its edx-platform images for building, collection, and watching. The script uses a mix of its own implementation and calls out to edx-platform's paver tasks, avoiding the most troublesome parts of the paver tasks. The script and its interface were the inspiration for the new build-assets.sh that this ADR describes.

As a consequence of this ADR, Tutor will either need to:

* reimplement the script as a thin wrapper around the new asset processing commands, or
* deprecate and remove the script.

**May 2024 update:** The ``openedx-assets`` script will be removed from Tutor,
with migration instructions documented in
`Tutor's changelog <https://github.com/overhangio/tutor/blob/master/CHANGELOG.md>`_.

non-Tutor migration guide
-------------------------

A migration guide for site operators who are directly referencing Paver will be
included in the
`Paver deprecation ticket <https://github.com/openedx/edx-platform/issues/34467>`_.

See also
********

OpenCraft has also performed a discovery on a `modernized system for static assets for XBlocks in xmodule <https://docs.google.com/document/d/1FqsvXpvrzsi2Ekk9RttUpcT2Eg0NxenFmV52US_psFU>`_. Its scope overlaps with this ADR's in a way that makes it great supplemental reading.

Rejected Alternatives
*********************

Live with the problem
======================

We could avoid committing any work to edx-platform asset tooling, and instead just wait until all frontends have been replatformed into MFEs. See the *Context* section above for why this was rejected.

Improve existing system
==========================

Rather than replace it, we could try to improve the existing Paver-based asset processing system. However, entirely dropping Paver and mostly dropping Python has promising benefits:

Asset build independence
------------------------

When building a container image, we want to be able to build static assets without first copying any Python code or requirements lists from edx-platform into the build context. That way, only changes to system requirements, npm requirements, or the assets themselves would trigger an asset rebuild.

Encouraging simplicity
----------------------

The asset pipeline only needs to perform a handful of simple tasks, primarily copying files and invoking shell commands. It does NOT need to be extensible, as we do not want new frontend features to be added to the edx-platform repository. On the contrary, simplicity and obviousness of implementation are virtues. Bash is particularly suited for these sort of scripts.

However, Python (like any modern application language) encourages developers to modularize, build abstractions, use clever control flow, and employ indirection. This is particularly noticeable with the Paver assets build, which is a thousand lines long and difficult to understand.

Better interop with standard tools
----------------------------------

It is best if the build can stem from a single call to ``npm install && npm run build`` rather than a call to a bespoke script (whether Paver or Bash). Generally speaking, the more edx-platform can work with standard frontend tooling, the easier it'll be for folks to use, understand, and maintain it.

