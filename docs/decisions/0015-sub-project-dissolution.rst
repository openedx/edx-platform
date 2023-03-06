Dissolution of edx-platform sub-projects
########################################

Status
******

Accepted

Context
*******

A "Python project" is a special folder that contains a "setup.py" file and gets installed using pip; the Python modules within it can be imported relative to said folder. Django projects typically define *one* Python project; in the case of Open edX, that project is almost always defined at the root of the containing repository. Of course, the project can be organized into hierarchial "Python packages", which are just folders containing Python code.

In contrast, edx-platform defined *seven* Python projects. One project was defined at the repository root, five "sub-projects" were defined in ./common/lib, and one additional sub-project was defined in ./openedx/core/lib/xblock_builtin. This:

* introduced unneeded complexity into the tooling, testing, and deployment of edx-platform;
* generated developer confusion due to the resulting abnormal import statements;
* created extra surface area for bugs; and
* limited our ability to statically analyze edx-platform.

Decision
********

The sub-projects were dissolved and their contents converted into typical Python packages (that is, folders within Python projects). Where feasible, they were be extracted into other repositories; where not, they were integrated into the edx-platform codebase in the way that seemed to be the least disruptive.

Consequences
************

General Implications
====================

* The edx-platform folder ./common/lib will be deleted. Its contents have been moved to various other locations. Some import paths have been changed in order to make this happen, as detailed below.

* There is a new top-level code directory in edx-platform: ./xmodule.

* Going forward, given an import in the form ``import <BLAH>`` in edx-platform, one can assume that either:

  * it’s importing from an external library, e.g. ``import requests``; or
  * ``<BLAH>`` represents the full path to the module, relative to the root of edx-platform, e.g. ``import xmodule.exception`` will import from ./xmodule/exceptions.py.

* The Python dependencies lists in edx-platform/requirements no longer point to any code in the local repository. This means that edx-platform Dockerfiles (or other sort of build recipes) no longer need to copy in edx-platform code before installing its requirements, which may have build caching benefits.

* There are some one-time tactial implications for developers and operators, which we attempted to capture `in a forum post <https://discuss.openedx.org/t/breaking-apart-edx-platforms-common-lib-folder/7556#implications-3>`_.

Detailed Code Changes
=====================

symmath
-------

* Before:

  * location: edx-platform/common/lib/symmath/symmath
  * usage: ``import symmath``

* After:

  * location: openedx-calc/symmath
  * usage: ``import symmath``

* PR: https://github.com/openedx/edx-platform/pull/29869

* Notes: This code thematically relates to openedx-calc repository and was easy to extract from edx-platform. It was important that its import path did not change, though, because instructor-authored code can import symmath, and that code would be very difficult to change across all Open edX instances.

safe_lxml
---------

* Before:

  * location: edx-platform/common/lib/safe_lxml/safe_lxml
  * usage: ``import safe_lxml``

* After:

  * location: edx-platform/openedx/core/lib/safe_lxml
  * usage: ``import openedx.core.lib.safe_lxml``

* PR: https://github.com/openedx/edx-platform/pull/25689

* Notes: safe_lxml is very small and specific to edx-platform, so extraction did not make sense. There were very few existing usages of safe_lxml, so changing its import path was not disruptive.

sandbox-packages (loncapa, verifiers, eia)
------------------------------------------

* Before:

  * location: edx-platform/common/lib/sandbox-packages/*
  * usage: ``import loncapa, verifiers, eia``

* After:

  * location: codejail-includes
  * usage: ``import loncapa, verifiers, eia``

* PR: https://github.com/openedx/edx-platform/pull/30402

* Notes: Extracting this folder was very easy because they had little-to-no dependence on edx-platform code. Additionally, this change reduces coupling of the "edx-sandbox" (codejail-powered safe execution environment) from edx-platform.

xmodule
-------

* Before:

  * location: edx-platform/common/lib/xmodule/xmodule
  * usage: ``import xmodule``

* After: 
  
  * location: edx-platform/xmodule
  * usage: ``import xmodule``

* PR: https://github.com/openedx/edx-platform/pull/30394

* Notes: We chose to move this folder to the repository root because:

  * it has many co-dependencies with the rest of edx-platform, so extraction was not an option; and
  * moving it to ./xmodule allowed the import path (``import xmodule``) to remain unchanged, which was helpful due to the large number of such imports both inside and outside of edx-platform.

capa
----

* Before:

  * location: edx-platform/common/lib/capa/capa
  * usage: ``import capa``

* After:

  * location: edx-platform/xmodule/capa
  * usage: ``import xmodule.capa``

* PR: https://github.com/openedx/edx-platform/pull/30403

* Notes: Like xmodule, extracting capa from edx-platform would have been difficult. However, updating its import path was feasible; so, to create avoid creating a sixth top-level package, it was decided to move the code within ./xmodule as a sub-packages. ./xmodule was chosen as the parent package because it contains related code, notably ./xmodule/capa_block.py, which defines the ``ProblemBlock`` (formerly the ``CapaModule``).

xblock_discussion
-----------------

* Before:

  * location: edx-platform/openedx/core/lib/xblock_builtin/xblock_discussion
  * usage: ``import xblock_discussion``

* After:

  * location: edx-platform/xmodule/discussion_block.py
  * usage: ``import xmodule.discussion_block``

* PR: https://github.com/openedx/edx-platform/pull/30636

* Notes: This project was essentially a stub that just defined the ``DiscussionBlock`` class. The block's actual implementation is still spread throughout edx-platform. Because all other baked-in XBlocks are defined in ./xmodule, it was decided to move the block's definition there as well.



Alternatives Considered
***********************

No alternatives were considered.

Further Reading
***************

These changes were `announced on the community forums <https://discuss.openedx.org/t/breaking-apart-edx-platforms-common-lib-folder/7556>`_ and `detailed futher in a public Jira epic <https://openedx.atlassian.net/browse/BOM-2579>`_.
