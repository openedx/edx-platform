Building static assets without Python
#####################################

Status
******

Pending

Will be moved to *Accepted* upon completion of re-implementation.

Context
*******

edx-platform assets (including legacy LMS views, legacy CMS views, and built-in XBlock views) are built using Python functions in the ``pavelib/`` directory. The build process includes:

* Copying files from ``node_modules/`` into various "vendor" directories to support RequireJS frontends.
* Collecting assets from XModule-style XBlocks that are built-in to the platform.
* Compiling common SCSS into CSS, both for base files and for theme-provided files.
* Running Webpack.
* Collecting assets into the ``STATIC_ROOT``.

Tutor invokes these functions via its custom `openedx-assets`_ Python script. Devstack and the old Ansible installation both invoke these functions via the ``paver update_assets`` command.

.. _openedx-assets: https://github.com/overhangio/tutor/blob/open-release/olive.1/tutor/templates/build/openedx/bin/openedx-assets.

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

