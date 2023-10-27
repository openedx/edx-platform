xmodule/assets: edx-platform XBlock resources
#############################################

This folder exists to contain resources (i.e., static assets) for the XBlocks
defined in edx-platform.

Concepts
********

We would like edx-platform XBlock resources to match the standard XBlock
resource strategy as much as possible, because:

* it'll make it easier to extract the XBlocks into their own packages
  eventually, and
* it makes it easier to reason about the system as a whole when
  internally-defined and externally-defined blocks play by the same rules.

Due to the legacy of the XModule system, we're not quite there yet.
However, we are proactively working towards a system where:

* Python is not involved in the generation of static assets.
* We minimze conditionals that differentiate between "older" (aka "XModule-style")
  XBlocks and newer (aka "pure") XBlocks.
* Each XBlock's assets are contained within their own folder as much as
  possible. See ``./vertical`` as an example.

Themable Sass (.scss)
*********************

XBlock CSS for ``student_view``, ``author_view``, and ``public_view`` is compiled from the various ``./<ClassName>BlockDisplay.scss`` modules, such as `AnnotatableBlockDisplay.scss`_.

XBlock CSS for ``studio_view`` is compiled from the various ``./<ClassName>BlockEditor.scss`` modules, such as `AnnotatableBlockEditor.scss`_.

Those Sass modules are mostly thin wrappers around the underscore-prefixed Sass
modules within block-type-subdirectories, such as `annotatable/_display.css`. In the
future, we may `simplify things`_ by collapsing the top-level Sass modules and
just directly compiling the block-type-subdirectories' Sass.

The CSS is compiled into the static folders of both LMS and CMS, as well as into
the corresponding folders in any enabled themes, as part of the edx-platform build.
It is collected into the static root, and then linked to from XBlock fragments by the
``add_sass_to_fragment`` function in `builtin_assets.py`_.

.. _AnnotatableBlockDisplay.scss: https://github.com/openedx/edx-platform/tree/master/xmodule/assets/AnnotatableBlockDisplay.scss
.. _AnnotatableBlockEditor.scss: https://github.com/openedx/edx-platform/tree/master/xmodule/assets/AnnotatableBlockEditor.scss
.. _annotatable/_display.scss: https://github.com/openedx/edx-platform/tree/master/xmodule/assets/annotatable/_display.scss
.. _simplify things: https://github.com/openedx/edx-platform/issues/32621


JavaScript (.js)
****************

Currently, edx-platform XBlock JS is defined both here in `xmodule/assets`_ and outside in `xmodule/js`_. Different JS resources are processed differently:

* For many older blocks, their JS is:

  * bundled using a `webpack.builtinblocks.config.js`_,
  * which is included into `webpack.common.config.js`_,
  * allowing it to be included into XBlock fragments using ``add_webpack_js_to_fragment`` from `builtin_assets.py`_.

  Example blocks using this setup:

  * `ProblemBlock`_
  * `HtmlBlock`_
  * `AnnotatableBlock`_

* For other "purer" blocks, the JS is used as a standard XBlock fragment. Example blocks:

  * `VerticalBlock`_
  * `LibraryContentBlock`_

As part of an `active build refactoring`_, we will soon consolidate all edx-platform XBlock JS here in `xmodule/assets`_.

.. _xmodule/assets: https://github.com/openedx/edx-platform/tree/master/xmodule/assets
.. _xmodule/js: https://github.com/openedx/edx-platform/tree/master/xmodule/js
.. _ProblemBlock: https://github.com/openedx/edx-platform/blob/master/xmodule/capa_block.py
.. _HtmlBlock: https://github.com/openedx/edx-platform/blob/master/xmodule/html_block.py
.. _AnnotatableBlock: https://github.com/openedx/edx-platform/blob/master/xmodule/annotatable_block.py
.. _VerticalBlock: https://github.com/openedx/edx-platform/blob/master/xmodule/vertical_block.py
.. _LibraryContentBlock: https://github.com/openedx/edx-platform/blob/master/xmodule/library_content_block.py
.. _active build refactoring: https://github.com/openedx/edx-platform/issues/31624
.. _builtin_assets.py: https://github.com/openedx/edx-platform/tree/master/xmodule/util/builtin_assets.py
.. _static_content.py: https://github.com/openedx/edx-platform/blob/master/xmodule/static_content.py
.. _library_source_block/style.css: https://github.com/openedx/edx-platform/blob/master/xmodule/assets/library_source_block/style.css
.. _webpack.builtinblocks.config.js: https://github.com/openedx/edx-platform/blob/master/webpack.builtinblocks.config.js
.. _webpack.common.config.js: https://github.com/openedx/edx-platform/blob/master/webpack.common.config.js
