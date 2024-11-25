xmodule
#######

The ``xmodule`` folder contains a variety of old-yet-important functionality core to both LMS and CMS, most notably:

* the ModuleStore, edx-platform's "Version 1" learning content storage backend;
* an XBlock Runtime implementation for ModuleStore-backed content;
* the "partitions" framework for differentiated XBlock content;
* implementations for the "stuctural" XBlocks: ``course``, ``chapter``, and ``sequential``;
* the implementations of several different built-in content-level XBlocks, such as ``problem`` and ``html``; and
* `assets for those built-in XBlocks`_.

.. _assets for those built-in XBlocks: https://github.com/openedx/edx-platform/tree/master/xmodule/assets#readme

Historical Context
******************

"XModule" was the original content framework for edx-platform, which gives the folder its current name.
XModules rendered specific course run content types to users for both authoring and learning.
For instance, there was an XModule for Videos, another for HTML snippets, and another for Sequences.

XModule was succeeded in ~2013 by the "XBlock" framework, which served the same purpose, but put additional focus into flexibility and modularity.
XBlock allows new content types to be created by anyone, completely external the edx-platform repository.
It remains the platform's flagship content plugin framework to this day.

For years, edx-platform supported both content frameworks simultaneously via a Frankenstein-ish hybrid XBlock+XModule runtime implementation in this directory.
Fortunately, in 2021, `all remaining XModules were converted into XBlocks`_.
Since support for the XModule framework is no longer necessary, `the BD-13 project`_ is now working to radically simplify the remaining XBlock runtime implementation.

This folder was moved from ./common/lib/xmodule/xmodule to its current location, ./xmodule. The reasons that this folder (along with several others) were moved are detailed in `this ADR about the dissolution of sub-projects`_.

.. _all remaining XModules were converted into XBlocks: https://discuss.openedx.org/t/xmodule-xblock-conversion-complete/4555
.. _the BD-13 project: https://openedx.atlassian.net/wiki/spaces/COMM/pages/3062333478/BD-13+xModule+--+xBlock+Conversion+Phase+2
.. _this ADR about the dissolution of sub-projects: https://github.com/openedx/edx-platform/blob/master/docs/decisions/0015-sub-project-dissolution.rst

Direction
*********

**Maintain, Simplify, Extract & Replace.**

Currently, this directory contains a lot of mission-critical functionality, so continued maintenance and simplification of it is important.
Still, we aim to eventually dissolve the directory in favor of more focused & decoupled subsystems:

<<<<<<< HEAD
* ModuleStore is superseded by the `Blockstore`_ storage backend.
* Blockstore-backend content is rendered by a new, simplified `edx-platform XBlock runtime`_.
=======
* ModuleStore is superseded by the `Learning Core`_ storage backend.
* Learning Core-backend content is rendered by a new, simplified `edx-platform XBlock runtime`_.
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
* Navigation, partitioning, and composition of learning content is being re-architected in the `openedx-learning`_ library.
* All new XBlocks are implemented in separate repositories, such as `xblock-drag-and-drop-v2`_.

To help with this direction, please **do not add new functionality to this directory**. If you feel that you need to add code to this directory, reach out on `the forums`_; it's likely that someone can help you find a different way to implement your change that will be more robust and architecturally sound!

<<<<<<< HEAD
.. _Blockstore: https://github.com/openedx/blockstore/
=======
.. _Learning Core: https://github.com/openedx/openedx-learning/
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
.. _edx-platform XBlock runtime: https://github.com/openedx/edx-platform/tree/master/openedx/core/djangoapps/xblock
.. _openedx-learning: https://github.com/openedx/openedx-learning
.. _xblock-drag-and-drop-v2: https://github.com/openedx/xblock-drag-and-drop-v2
.. _the forums: https://discuss.openedx.org

