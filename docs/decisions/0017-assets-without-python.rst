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
   * - **XBlock Fragments**
     - JS and CSS belonging to the pure XBlocks defined in edx-platform
     - library_sourced_block.js
     - Keep, or extract to per-XBlock repositories
   * - **XModule Fragments**
     - JS and SCSS belonging to the older XModule-style XBlocks defined in edx-platform
     - ProblemBlock (aka CAPA) assets
     - Convert to pure XBlock fragments
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
   * - **pip-installed Assets**
     - Pre-compiled static assets shipped with several Python libraries that we install, including XBlocks. Not committed to edx-platform.
     - Django Admin, Swagger, Drag-And-Drop XBlock V2
     - Keep
   * - **npm-installed Assets**
     - JS modules and CSS files installed via NPM. Not committed to edx-platform.
     - React
     - Remove as part of full LMS/CMS frontend replatforming

(Note that this table excludes HTML templates. Templates are part of the frontend, but they are dynamically rendered by the Web application and therefore must be handled differently than static assets.)

So with the exception of XBlock fragments and pip-installed assets, which are very simple for edx-platform to handle, we plan to eventually remove all edx-platform static frontend assets. However, given the number of remaining edx-platform frontends and speed at which they are currently being replatformed, estimates for completion of this process range from one to five years. Thus, in the medium term future, we feel that timeboxed improvements to how edx-platform handles static assets are worthwhile.

Types of asset processing
=========================

There are three actions a developer or a deployment pipeline may need to take on edx-platform static assets:

* **Build:** Compile, generate, copy, and otherwise process static assets so that they can be used by the Django webserver or collected elsewhere. For many Web applications, all static asset building would be coordinated via Webpack or another NPM-managed tool. Due to the age of edx-platform and its legacy XModule and Comprehensive Themeing systems, though, there are five specific build steps, which generally need to be performed in this  order:

  #. **Copy NPM-installed assets** from node_modules to places where they can be used by certain especially-old edx-platform frontends that do not work with NPM.

  #. **Copy XModule assets** from the xmodule source tree over to places where will be available for Webpacking and SCSS compliation.

  #. **Run Webpack** to shim, minify, and bundle JS modules.

  #. **Compile Default SCSS** into CSS.

  #. **Compile Theme SCSS** into CSS from some number of operator-specified theme directories, using default SCSS as a base.

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

