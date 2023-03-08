Reimplement edx-platform static asset processing
################################################

Overview
********

* edx-platform has a complicated process for managing its static frontend assets. It slows down both developers and site operators.
* We will deprecate the current Python+paver asset processing system in favor of a new Bash implementation.
* After one named release, the deprecated paver system will be removed.

Status
******

**Provisional**

The status will be moved to *Accepted* upon completion of reimplementation. Related work:

* `[DEPR]: Asset processing in Paver <https://github.com/openedx/edx-platform/issues/31895>`_
* `Process edx-platform assets without Paver <https://github.com/openedx/edx-platform/issues/31798>`_
* `Process edx-platform assets without Python <https://github.com/openedx/edx-platform/issues/31800>`_


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
* When Django/Python is absolutely required, contain its impact so that the rest of the system remains Python-free.
* Avoid unnecessary indirection or abstraction. For this task, extensibility is a non-goal, and simplicity is a virtue.
* Provide a clear migration path from the old system to the new one.
* Enable the future removal of as much legacy frontend tooling code as possible.

Consequences
************

Reimplementation Specification
==============================

The three top-level edx-platform asset processing actions are *build*, *collect*, and *watch*. The build action can be further broken down into five stages. Here is how those actions and stages will be reimplemented:


.. list-table::
   :header-rows: 1

   * - Description
     - Old implementation
     - New implementation

   * - **Build: All stages.** Compile, generate, copy, and otherwise process static assets so that they can be used by the Django webserver or collected elsewhere. For many Web applications, all static asset building would be coordinated via Webpack or another NPM-managed tool. Due to the age of edx-platform and its legacy XModule and Comprehensive Theming systems, though, there are five stages which need to be performed in a particular order.

     - ``paver update_assets --skip-collect``

       A Python-defined task that calls out to each build stage.

     - ``scripts/build-assets.sh``

       A Bash script that contains all build stages, with subcommands available for running each stage separately. Its command-line interface inspired by Tutor's ``openedx-assets`` script. The script will be runnable on any POSIX system, including macOS and Ubuntu and it will linted for common shell scripting mistakes using `shellcheck <https://www.shellcheck.net>`_.
     
   * - + **Build stage 1: Copy npm-installed assets** from node_modules to other folders in edx-platform. They are used by certain especially-old legacy LMS & CMS frontends that are not set up to work with npm directly.

     - ``paver update_assets --skip-collect``

       Implemented in Python within update_assets. There is no standalone command for it.

     - ``scripts/build-assets.sh npm``

       Pure Bash reimplementation. See *Rejected Alternatives* for a note about this.
 
   * - + **Build stage 2: Copy XModule fragments** from the xmodule source tree over to input directories for Webpack and SCSS compilation. This is required for a hard-coded list of old XModule-style XBlocks. This is not required for new pure XBlocks, which include (or pip-install) their assets into edx-platform as ready-to-serve JS/CSS/etc fragments.

     - ``paver process_xmodule_assets``, or

       ``xmodule_assets``

       Equivalent paver task and console script, both pointing at to an application-level Python module. That module inspects attributes from legacy XModule-style XBlock classes in order to determine which static assets to copy and what to name them.

     - ``scripts/build-assets.sh xmodule``

       A Bash implementation of XModule asset copying. The aforementioned attributes will be moved from the XModule-style XBlock classes into a simple static JSON file, which the Bash script will be able to read.
       
       The initial implementation of build-assets.sh may just point the existing ``xmodule_assets`` script.

       Eventually, if possible, it would be desirable to `entirely remove this step <https://github.com/openedx/edx-platform/issues/31624>`_.
   
   * - + **Build stage 3: Run Webpack** in order to to shim, minify, otherwise process, and bundle JS modules. This requires a call to the npm-installed ``webpack`` binary.

     - ``paver webpack``

       Python wrapper around a call to webpack. Invokes the ``./manage.py [lms|cms] print_setting`` multiple times in order to determine Django settings, adding which can add 20+ seconds to the build.

     - ``scripts/build-assets.sh webpack $(./manage.py lms print_asset_settings)``

       Bash wrapper around a call to webpack. The script will accept parameters for Django settings rather than looking them up.

       The print_asset_settings management command will be added as well. It will print the set of Django settings needed for the asset build in a way that build-assets.sh can accept as input. Some distributions may not need to call this command; Tutor, for example, will probably render the settings directly into the build-assets.sh call.
   
   * - + **Build stage 4: Compile default SCSS** into CSS for legacy LMS/CMS frontends.

     - ``paver compile_sass``

       Paver task that invokes ``sass.compile`` (from the libsass Python package) and ``rtlcss`` (installed by npm) for several different directories of SCSS.

       Note: libsass is pinned to a 2015 version with a non-trivial upgrade path. Installing it requires compiling a large C extension, noticeably affecting Docker image build time.

     - ``scripts/build-assets.sh css``

       Bash reimplementation, calling ``node-sass`` and ``rtlcss``.
   
       The initial implementation of build-assets.sh may use ``sassc``, a CLI provided by libsass, instead of node-sass. Then, ``sassc`` can be replaced by ``node-sass`` as part of a subsequent `edx-platform frontend framework upgrade effort <https://github.com/openedx/edx-platform/issues/31616>`_.

   * - + **Build stage 5: Compile themes' SCSS** into CSS for legacy LMS/CMS frontends. The default SCSS is used as a base, and theme-provided SCSS files are used as overrides. Themes are searched for from some number of operator-specified theme directories.

     - ``./manage.py [lms|cms] compile_sass``, or

       ``paver compile_sass --theme-dirs ...``

       The management command is a wrapper around the paver task. The former looks up the list of theme search directories from Django settings and site configuration; the latter requires them to be supplied as arguments.

     - ``./manage.py [lms|cms] compile_sass``, or

       ``scripts/build-assets.sh themes --theme-dirs ...``

       The management command will remain available, but it will need to be updated to point at the Bash script, which will replace the paver task (see build stage 4 for details).

       The overall asset *build* action will use the Bash script; this means that list of theme directories will need to be provided as arguments, but it ensures that the build can remain Python-free.
   
   * - **Collect** the built static assets from edx-platform to another location (the ``STATIC_ROOT``) so that they can be efficiently served *without* Django's webserver. This step, by nature, requires Python and Django in order to find and organize the assets, which may come from edx-platform itself or from its many installed Python and NPM packages. This is only needed for **production** environments, where it is usually desirable to serve assets with something efficient like NGINX.

     - ``paver update_assets``

       Paver task wrapping a call to the standard Django `collectstatic <https://docs.djangoproject.com/en/4.1/ref/contrib/staticfiles/#collectstati>`_ command. It adds ``--noinput`` and a list of ``--ignore`` file patterns to the command call.

       (This command also builds assets. The *collect* action could not be run on its own without calling pavelib's Python interface.)

     - ``./manage.py lms collectstatic --noinput && ./manage.py cms collectstatic --noinput``

       The standard Django interface will be used without a wrapper. The ignore patterns will be added to edx-platform's `staticfiles app configuration <https://docs.djangoproject.com/en/4.1/ref/contrib/staticfiles/#customizing-the-ignored-pattern-list>`_ so that they do not need to be supplied as part of the command.
   
   * - **Watch** static assets for changes in the background. When a change occurs, rebuild them automatically, so that the Django webserver picks up the changes. This is only necessary in **development** environments. A few different sets of assets may be watched: XModule fragments, Webpack assets, default SCSS, and theme SCSS.

     - ``paver watch_assets``

       Paver task that invokes ``webpack --watch`` for Webpack assets and watchdog (a Python library) for other assets.

     - ``scripts/build-assets.sh --watch <stage>``

       (where ``<stage>`` is optionally one of the build stages described above. If provided, only that stage's assets will be watched.)

       Bash wrappers around invocation(s) of `watchman <https://facebook.github.io/watchman/>`_, a popular file-watching library maintained by Meta. Watchman is already installed into edx-platform (and other services) via the pywatchman pip wrapper package.

       Note: This adds a Python dependency to build-assets.sh. However, we could be clear that watchman is an *optional* dependency of build-assets.sh which enables the optional ``--watch`` feature. This would keep the *build* action Python-free. Alternatively, watchman is also available Python-free via apt and homebrew.

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

Either way, the migration path is straightforward:

.. list-table::
   :header-rows: 1

   * - Existing Tutor-provided command
     - New upstream command
   * - ``openedx-assets build``
     - ``scripts/build-assets.sh``
   * - ``openedx-assets npm``
     - ``scripts/build-assets.sh npm``
   * - ``openedx-assets xmodule``
     - ``scripts/build-assets.sh xmodule``
   * - ``openedx-assets common``
     - ``scripts/build-assets.sh css``
   * - ``openedx-assets themes``
     - ``scripts/build-assets.sh themes``
   * - ``openedx-assets collect``
     - ``./manage.py [lms|cms] collectstatic --noinput``
   * - ``openedx-assets watch-themes``
     - ``scripts/build-assets.sh --watch themes``

The options accepted by ``openedx-assets`` will all be valid inputs to ``scripts/build-assets.sh``.

See also
********

OpenCraft has also performed a discovery on a `modernized system for static assets for XBlocks in xmodule <https://docs.google.com/document/d/1FqsvXpvrzsi2Ekk9RttUpcT2Eg0NxenFmV52US_psFU>`_. Its scope overlaps with this ADR's in a way that makes it great supplemental reading.

Rejected Alternatives
*********************

Copy node_modules via npm post-install
======================================

It was noted that `npm supports lifecycle scripts <https://docs.npmjs.com/cli/v6/using-npm/scripts#pre--post-scripts>`_ in package.json, including ``postinstall``. We could use a post-install script to copy assets out of node_modules; this would occurr automatically after ``npm install``. Arguably, this would be more idiomatic than this ADR's proposal of ``scripts/build-assets.sh npm``.

For now, we decided against this. While it seems like a good potential future improvement, we are currently unsure how it would interact with `moving node_modules out of edx-platform in Tutor <https://github.com/openedx/wg-developer-experience/issues/150>`_, which is a motivation behind this ADR. For example, if node_modules could be located anywhere on the image, then we are not sure how the post-install script could know its target directory without us hard-coding Tutor's directory structure into the script.

Live with the problem
======================

We could avoid committing any work to edx-platform asset tooling, and instead just wait until all frontends have been replatformed into MFEs. See the *Context* section above for why this was rejected.

Improve existing system
=======================

Rather than replace it, we could try to improve the existing Paver-based asset processing system. However, the effort required to do this seemed comparable to the effort required to perform a full rewrite, and it would not yield any caching benefits of a Python-free asset pipeline.

Rewrite asset processing in Python
==================================

Some of the benefits of dropping Paver could still be achieved even if we re-wrote the asset processing system using, for example, Python and Click. However, entirely dropping Python from the asset build in favor of Bash has promising benefits:

Asset build independence
------------------------

When building a container image, we want to be able to build static assets without first copying any Python code or requirements lists from edx-platform into the build context. That way, only changes to system requirements, npm requirements, or the assets themselves would trigger an asset rebuild.

Encouraging simplicity
----------------------

The asset pipeline only needs to perform a handful of simple tasks, primarily copying files and invoking shell commands. It does NOT need to be extensible, as we do not want new frontend features to be added to the edx-platform repository. On the contrary, simplicity and obviousness of implementation are virtues. Bash is particularly suited for these sort of scripts.

However, Python (like any modern application language) encourages developers to modularize, build abstractions, use clever control flow, and employ indirection. This is particularly noticeable with the Paver assets build, which is a thousand lines long and difficult to understand.

Ease of transition to standard tools
------------------------------------

Ideally, the entire asset build would stem from a call to ``npm build`` rather than a call to a bespoke script (whether Paver or Bash). Generally speaking, the more edx-platform can work with standard frontend tooling, the easier it'll be for folks to use, understand, and maintain it.

When bespoke asset building logic is implemented in Bash, it is easier to integrate or replace that logic with a standard tool. Standard JS tools often can run hooks written in JS or Shell. On the other hand, frontend tools typically do not integrate with Python scripts.

