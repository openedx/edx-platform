#######################################
edx-platform Static Asset Pipeline Plan
#######################################

Static asset handling in edx-platform has evolved in a messy way over the years.
This has led to a lot of complexity and inconsistencies. This is a proposal for
how we can move forward to a simpler system and more modern toolchain. Note that
this is not a detailed guide for how to write React or Bootstrap code. This is
instead going to talk about conventions for how we arrange, extract, and compile
static assets.

Big Open Questions (TODO)
*************************

This document is a work in progress, as the design for some of this is still in
flux, particularly around extensibility.

* Pluggable third party apps and Webpack packaging.
* Keep the Django i18n mechanism?
* Stance on HTTP/2 and bundling granularity.
* Optimizing theme assets.
* Tests

Requirements
************

Any proposed solution must support:

* Externally developed and installed Django apps.
* Theming.
* XBlock assets.
* Existing tests.
* Fast builds.
* An incremental implementation path.
* Other kinds of pluggability???

Assumptions
***********

Some assumptions/opinions that this proposal is based on:

* We want to shift as much as possible to Webpack and the JavaScript stack of
  technologies, leaving the Python layer as thin as possible.
* While we will try to make theming upgrades straightforward, we will be moving
  around where files are located and where they're compiled out to.
* We will be pushing towards a world that is more Django app-centric than LMS
  vs. Studio centric, to reduce duplication.
* At the same time, we want to consolidate assets far more efficiently than we
  are doing today.
* Leaning towards more static front ends + API calls.
* However we still need to be compatible with Django's asset system for things
  like third party apps (e.g. Django Rest Framework browsing assets, Swagger,
  etc.)
* It should be possible to pre-build static assets and deploy them onto S3 or
  similar.

Where We Are Today
******************

We have a static asset pipeline that is mostly driven by Django's built-in
staticfiles finders and the collectstatic process. We use the popular
``django-pipeline`` library, with UglifyJS as the JavaScript compressor (the
binary is installed via node into node_modules). We also use the less well known
``django-pipeline-forgiving`` extension to ``django-pipeline`` so we don't error
out when files are missing (added when we started dynamically scanning XBlocks
for assets).

The ``django-pipeline`` config is aware of CSS files for the purposes of
concatenation, but it does *not* know about the source Sass files.
Those are processed with paver tasks before ``django-pipeline`` ever sees them.

We also have the following custom extensions to Django's builtin ``STATICFILES``
mechanism:

``openedx.core.djangoapps.theming.finders.ThemeFilesFinder``
  Custom finder that overrides any static asset with a version from the themes
  directory (``COMPREHENSIVE_THEME_DIRS`` defined in ``lms.yml`` and
  ``studio.yml``).

``openedx.core.lib.xblock_pipeline.finder.XBlockPipelineFinder``
  Custom finder that accesses and extracts assets from pip-installed XBlocks via
  ``pkg_resources``.

``openedx.core.storage.DevelopmentStorage/ProductionStorage``
  Custom ``FileStorage`` classes that mostly exist for theme-awareness.

LMS and Studio/CMS Separation
-----------------------------

LMS and Studio have their own directories for source assets (``lms/static`` and
``cms/static``), and have symlinks to shared assets in ``common/static``. We
treat the static asset compilation and collection phase for LMS and Studio as
separate projects that happen to share a lot of pieces. They output to different
places (typically ``/edx/var/edxapp/staticfiles`` for LMS and
``/edx/var/edxapp/staticfiles/studio`` for Studio) and can be collected
separately. However in practice they're always run together because we deploy
them from the same commits and to the same servers.
 
Django vs. Webpack Conventions
******************************

The Django convention for having an app with bundled assets is to namespace them
locally with the app name so that they get their own directories when they are
gathered together into a common static directory by collectstatic. For example,
the edx-enterprise app has a ``static/enterprise`` folder, so its assets are
compiled to ``/edx/var/edxapp/staticfiles/enterprise`` by edx-platform and will
not conflict with assets from any other Django app.

Webpack conventions would have us create a single set of configuration files at
the root of edx-platform, which would specify all bundles in the project.

TODO: The big, "pluggable Webpack components" question.

Proposed Repo Structure
***********************

All assets that are in common spaces like ``common/static``, ``lms/static``,
and ``cms/static`` would be moved to be under the Django apps that they are a
part of and follow the Django naming convention (e.g.
``openedx/features/course_bookmarks/static/course_bookmarks``). An app's
``templates/{appname}`` directory will only be for server side templates, and
any client-side templates will be put in ``static/{appname}/templates``.

Proposed Compiled Structure
***************************

This is meant to be a sample of the different types of things we'd have, not a
full list:

::

  # Webpack bundles/post-processed assets
  /webpack/css
          /fonts
          /js
          /vendor ?

  # Django apps that are in the edx-platform repo
  /course_bookmarks
  /course_experience

  # edX authored, installed via separate repo
  /enterprise

  # Entirely third party apps that we need to maintain compatiblity with.
  /admin
  /rest_framework

  # Themes are part of the "theming" app
  /theming/themes/open-edx
                 /red-theme
                 /edx.org
  
  # XBlocks still collect their assets into a common space (/xmodule goes away)
  # We consider this to be the XBlock Runtime's app, and it collects static
  # assets from installed XBlocks.
  /xblock

Django vs. Webpack Roles
************************

Rule of thumb: Django/Python still serves static assets, Webpack processes and
optimizes them.

Webpack would be responsible for all Sass compilation in edx-platform. It would
also be responsible for the optimization/minification of JavaScript assets, but
those optimized assets would only appear under the ``/webpack`` directory. Third
party assets that Webpack is not aware of may have hash suffixes applied to them
by the Django collectstatic layer, but will not otherwise be processed or
optimized in any way -- so no sass compilation, no uglifyjs minification, etc.

The django-pipeline dependency should be removed altogether.

Themes
------

Theme handling is muddled. The fact that themes can override server-side
templates means that Python has to be aware of them. At the same time, we want
to shift over Sass compilation as a whole to Webpack, meaning that at least some
knowledge about where they are and how to compile them has to exist there. Also,
there are JS assets in some themes that provide additional functionality, and it
would be a performance degradation if those assets were no longer optimized.

What I do NOT want to happen:

* Significant end user performance degradation.
* Having an *additional* system in the asset pipeline (e.g. keeping
  django-pipeline around while having additional systems).

I think that means that conceptually, there exists a larger Static Asset system
that exists and that we think of both Webpack and Django being consumers of its
configuration. This is also very fuzzy at the moment.

Asset Groups
------------

There will be logical groupings of static assets. There should be uniformity and
no duplication within a group, but we would allow duplication between groups to
better facilitate independent deployment and isolation.

Example Groups:

* XBlock/XModule Assets
* LMS/Studio apps in edx-platform
* Third party app, such as edx-enterprise
