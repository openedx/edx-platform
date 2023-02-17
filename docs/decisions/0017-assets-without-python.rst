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
     - Course outline editor and unit editor
     - Replatform & DEPR
   * - **Shared Frontend Files**
     - JS modules, SCSS partials, and other resources, usable by both Legacy LMS and CMS Frontends. This includes a few libraries that have been committed to edx-platform in their entirety.
     - Legacy cookie policy banner; CodeMirror
     - Remove as part of full LMS/CMS frontend replatforming
   * - **npm-installed Assets**
     - JS modules and CSS files installed via NPM. Not committed to edx-platform.
     - React
     - Remove as part of full LMS/CMS frontend replatforming
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

Decision
********

We will rewrite edx-platform's asset processing system. We will aim to:

* Use well-known, npm-installed frontend tooling wherever possible.
* When bespoke processing is required, use standard POSIX tools like Bash.
* When Django/Python is absolutely required, contain its impact so that the rest of the system remains Python-free.
* Avoid unnecessary indirection or abstraction. For this task, extensibility is a non-goal, and simplicity is a virtue.
* Provide a clear migration path from the old system to the new one.
* Enable the future removal of as much legacy frontend tooling code as possible.

Consequences
************

The three top-level edx-platform asset processing actions are *build*, *collect*, and *watch*. The build action can be further broken down into five stages. Here is how those actions and stages will change:


.. list-table::
   :header-rows: 1

   * - Action/Stage
     - Description
     - Old implementation
     - New implementation

   * - **Build**
     - Compile, generate, copy, and otherwise process static assets so that they can be used by the Django webserver or collected elsewhere. For many Web applications, all static asset building would be coordinated via Webpack or another NPM-managed tool. Due to the age of edx-platform and its legacy XModule and Comprehensive Theming systems, though, there are five stages which need to be performed in a particular order.
     - ``paver update_assets``: yada
     - ``assets/build.sh``

TODO
====

There are three actions a developer or a deployment pipeline may need to take on edx-platform static assets:

* **Build:** :

  #. **Copy npm-installed assets** from node_modules to other folders in edx-platform. They are used by certain especially-old legacy LMS & CMS frontends that are not set up to work with npm directly.

  #. **Copy XModule Fragments** from the xmodule source tree over to places where will be available for Webpacking and SCSS compliation. This is done for a hard-coded list of XModule-style XBlocks, which are not growing in number; it is *not* a problem for in-repository pure XBlock Fragments or pip-installed XBlock assets, which are ready-to-serve.

  #. **Run Webpack** to shim, minify, and bundle JS modules. This requires a call to the npm-installed ``webpack`` binary.

  #. **Compile Default SCSS** for legacy LMS and CMS frontends into CSS.

  #. **Compile Theme SCSS** for legacy LMS and CMS frontends into CSS. The default SCSS is used as a base, and theme-provided SCSS files are used as overrides. Themes are searched for from some number of operator-specified theme directories.

* **Collect:** Copy static assets from edx-platform to another location (the ``STATIC_ROOT``) so that they can be efficiently served *without* Django's webserver. This step, by nature, requires Python and Django in order to find and organize the assets, which may come from edx-platform itself or from its many installed Python and NPM packages. This is only done for production environments, where it is usually desirable to serve assets with something efficient like NGINX.

* **Watch:** Listen for changes to static assets in the background. When a change occurs, rebuild them automatically, so that the Django webserver picks up the changes. This is only necessary in development environments. A few different sets of assets can be watched:

  * XModule assets. Upon change, these should be re-copied, which should trigger a Webpack re-run and a defualt SCSS recompilation.

  * JavaScript modules. Upon change, a Webpack re-run should be triggered.

  * Default SCSS. Upon change, it should be re-compiled, as should theme SCSS.

  * Theme SCSS. Upon change, it should be re-compiled.

Entry points for asset processing
=================================

Today, there are two main ways an operators would perform these actions:

* via edx-platform's ``paver`` command-line interface (defined in the `pavelib`_ source tree), which wraps all the actions in Python, and requires Django. Example usage, via Devstack::

    make lms-shell
    paver update_assets

* via the `openedx-assets`_ script, which Tutor adds to LMS and CMS containers. It uses a mix of its own Python wrapper code and calls to the pavelib implementation mentioned above. It avoids parts of pavelib that Tutor's authors found slow or buggy. Example usage::

    tutor dev run lms openedx-assets --env=dev

Python used in the asset build
==============================

.

Etc
===

.. _paver: https://github.com/openedx/tutor/tree/open-release/olive.1/pavelib
.. _openedx-assets: https://github.com/overhangio/tutor/blob/v15.0.0/tutor/templates/build/openedx/bin/openedx-assets.

Updating the asset build pipeline will be necessary for several current and upcoming efforts, including:

* `Finish upgrading frontend frameworks <https://github.com/openedx/edx-platform/issues/31616>`_
* `Move node_modules outside of edx-platform in Tutor's openedx image <https://github.com/openedx/wg-developer-experience/issues/150>`_
* `Move static assets outside of edx-platform in Tutor's openedx image <https://github.com/openedx/wg-developer-experience/issues/151>`_

This has caused us to consider the value of updating the asset pipeline in place, versus rewriting and simplying it first.

Decision
********

TODO

Rationale:

    * Other parts of pavelib have already been reimplemented, like Python
      unit tests. We're following that trend.
    * The Python logic in pavelib is harder to understand than simple
      shell scripts.
    * pavelib has dependencies (Python, paver, edx-platform, other libs)
      which means that any pavelib scripts must be executed later in
      the edx-platform build process than we might want them to. For
      example, in a Dockerfile, it might be more performant to process
      npm assets *before* installing Python, but as long as we are still
      using pavelib, that is not an option.
    * The benefits of paver have been eclipsed by other tools, like
      Docker (for requisite management) and Click (for CLI building).
    * In the next couple commits, we make improvements to
      process-npm-assets.sh. These improvements would have been possible
      in the pavelib implementation, but would have been more complicated.
...

Consequences
************

TODO

...

Alternatives Considered
***********************

TODO

...

