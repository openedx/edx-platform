xmodule/static: edx-platform XBlock assets
##########################################

Current State: SCSS only
************************

This folder exists to contain frontend static assets for the XBlocks defined in edx-platform. Its current structure is:

* ``./sass/lms/``: Top-level SCSS modules for student, author, and public views of XModules. Based on LMS styles.
* ``./sass/cms/``: Top-level SCSS modules for the Studio editor views of XModules. Based on CMS styles.
* ``./sass/include/``: SCSS modules shared between ``./sass/lms/`` and ``./sass/cms/``.
* ``./css/``: Git-ignored target for CSS, compiled from ``./sass/lms/`` and ``./sass/cms/``.

CSS files for XModules are added to Webpack at runtime using the custom ``XModuleWebpackLoader`` defined in `xmodule_django`_. From Webpack, they are included into individual XModules using ``add_webpack_to_fragment``, defined in that same module.

Please note that *XModules* in this context refers to a set of old XBlocks in edx-platform which inherit from ``HTMLSnippet`` and use a special legacy asset processing system. Examples include:

* `ProblemBlock`_
* `HtmlBlock`_
* `AnnotatableBlock`_

There are a handful of XBlocks in edx-platform that do *not* use this legacy static asset system; for example:

* `VerticalBlock`_
* `LibrarySourcedBlock`_

Future: Both SCSS and JS
************************

This folder is the target of `an active build refactoring project`_.

* Currently, edx-platform XBlock JS is defined in both ``xmodule/js/`` and ``xmodule/assets/``.

  * For XModules, their JS is copied to ``common/static/xmodule`` by ``xmodule/static_content.py`` (aka ``xmodule_assets``), and then bundled using a generated Webpack config at ``common/static/xmodule/wepack.xmodule.config.js``.
  * For the non-XModule blocks, the JS is used as a standard XBlock fragment.
  * The JS is also built into a couple different places, seemingly for testing purposes, in ways that are not yet completely understood. This is under investigation.

* As part of the active refactoring:

  * we will stop the special copying process in ``xmodule_assets``, and instead use the XModule JS directly;
  * we will move ``webpack.xmodule.config.js`` here instead of generating it;
  * we will consolidate all edx-platform XBlock JS here;
  * we will simplify any remaining build XBlock JS build processes & document them here.

* Further in the future, we may drop the special XModule SCSS and JS bundling entirely, and turn all resources into standard XBlock fragments.

.. _xmodule_django: https://github.com/kdmccormick/edx-platform/blob/master/xmodule/util/xmodule_django.py
.. _ProblemBlock: https://github.com/kdmccormick/edx-platform/blob/kdmccormick/xmodule-static-css/xmodule/capa_block.py
.. _HtmlBlock: https://github.com/kdmccormick/edx-platform/blob/kdmccormick/xmodule-static-css/xmodule/html_block.py
.. _AnnotatableBlock: https://github.com/kdmccormick/edx-platform/blob/kdmccormick/xmodule-static-css/xmodule/annotatable_block.py
.. _VerticalBlock: https://github.com/kdmccormick/edx-platform/blob/kdmccormick/xmodule-static-css/xmodule/vertical_block.py
.. _LibrarySourcedBlock: https://github.com/kdmccormick/edx-platform/blob/kdmccormick/xmodule-static-css/xmodule/library_sourced_block.py
.. _an active build refactoring project: https://github.com/openedx/edx-platform/issues/31624
