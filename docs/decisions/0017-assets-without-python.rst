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
     - + Switch from large, legacy tooling packages (such as libsass-python and paver) to industry standard, precompiled ones (like node-sass or dart-sass).
       + Remove unneccessary & slow calls to Django management commands.

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
     - ``assets/build.sh``: A Bash script that contains all build stages, its command-line interface inspired by Tutor's ``openedx-assets`` script. The script will be runnable on any POSIX system, including macOS and Ubuntu. The script will be linted for common shell scripting mistakes using `shellcheck <https://www.shellcheck.net>`_.
     
   * - **Build stage 1: Copy npm-installed assets** from node_modules to other folders in edx-platform. They are used by certain especially-old legacy LMS & CMS frontends that are not set up to work with npm directly.
     - N/A (part of ``paver update_assets``)
     - ``assets/build.sh npm``: TODO
   
   * - **Build stage 2: Copy XModule framents** from the xmodule source tree over to places where will be available for Webpacking and SCSS compliation. This is done for a hard-coded list of XModule-style XBlocks, which are not growing in number; it is *not* a problem for in-repository pure XBlock Fragments or pip-installed XBlock assets, which are ready-to-serve.
     - ``paver process_xmodule_assets`` and ``xmodule_assets``. The former is a Python wrapper of the latter; the latter is a console script pointing to an application-level Python module. That module inspects attributes from legacy XModule-style XBlock classes in order to determine which static assets to copy and what to name them.
     - ``assets/build.sh xmodule``: A Bash implementation of XModule asset copying. The aforementioned attributes will be moved from the XModule-style XBlock classes into a simple static JSON file, which the Bash script will be able to read.
   
   * - **Build stage 3: Run Webpack** in order to to shim, minify, otherwise process, and bundle JS modules. This requires a call to the npm-installed ``webpack`` binary.
     - ``paver webpack``: A Python wrapper around a call to webpack. Invokes the ``./manage.py [lms|cms] print_setting`` multiple times in order to determine Django settings, adding which can add 20+ seconds to the build.
     - ``assets/build.sh webpack``, a Bash wrapper around a call to webpack. The script will accept parameters for Django settings rather than looking them up. Open edX distributions, such as Tutor, can choose how to supply the Django-setting-dervied parameters in an efficient manner.
   
   * - **Build stage 4: Compile default SCSS** into CSS for legacy LMS/CMS frontends.
     - ``paver compile_sass``: TODO. Mention libsass.
     - ``assets/build.sh common``: TODO
   
   * - **Build stage 5: Compiled themes' SCSS** into CSS for legacy LMS/CMS frontends. The default SCSS is used as a base, and theme-provided SCSS files are used as overrides. Themes are searched for from some number of operator-specified theme directories.
     - ``paver compile_sass``: TODO
     - ``assets/build.sh themes``: TODO
   
   * - **Collect** the built static assets from edx-platform to another location (the ``STATIC_ROOT``) so that they can be efficiently served *without* Django's webserver. This step, by nature, requires Python and Django in order to find and organize the assets, which may come from edx-platform itself or from its many installed Python and NPM packages. This is only done for production environments, where it is usually desirable to serve assets with something efficient like NGINX.
     - ``paver update_assets``: TODO
     - ``./manage.py lms collectstatic && ./manage.py cms collectstatic``: TODO
   
   * - **Watch** static assets for changes in the background. When a change occurs, rebuild them automatically, so that the Django webserver picks up the changes. This is only necessary in development environments. A few different sets of assets may be watched: XModule assets, Webpack assets, default SCSS, and theme SCSS.
     - ``paver watch_assets``: TODO
     - ``assets/build.sh --watch <stage>``, where ``<stage`` if one of the build stages described above. TODO.

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

