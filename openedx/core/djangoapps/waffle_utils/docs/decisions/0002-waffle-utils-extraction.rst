Waffle Utils Extraction
***********************

Status
======

Accepted

Context
=======

The waffle utilities in this app were created in edx-platform, but are generally useful across IDAs.

Decision
========

These utilities will be be moved to `edx/edx-toggles`_ so that they can be used by other IDAs. Additionally, the shared library will use the module name ``toggles``, rather than ``waffle_utils``, so it can more generally include non-waffle based toggle utilities as well.

.. _edx/edx-toggles: https://github.com/edx/edx-toggles

Consequences
============

* Rollout plan required to deprecate and update class references.
* See ADR 0003-leave-course-waffle-flag for the decision to leave the CourseWaffleFlag behind.
* See ADR 0004-waffle-util-namespacing for decision to change namespacing implementation before extraction.
* The toggle state endpoint, which is meant to be a Django Plugin, could be extracted as a separate step. This requires some additional work:

  * Finishing out work around Django Plugin capabilities in edx-django-utils.
  * Adding ability to document CourseWaffleFlag from edx-platform. Note: we may lose the ability to find course override data for toggles no longer in use, by looping through the entire model, unless we add a hook for this from the edx-toggles version.

* The helper `get_instance_module_name`_ should probably move to `edx_django_utils/monitoring/code_owner`_. It could be considered hacky, but is quite useful. It needs to work whether the class definition is in a library or an IDA, and whether the instance declaration is in a library or an IDA.

.. _get_instance_module_name: https://github.com/edx/edx-platform/blob/a8c3413a32510dc45301d0c462bf706a5f7ba487/openedx/core/djangoapps/waffle_utils/__init__.py#L521
.. _edx_django_utils/monitoring/code_owner: https://github.com/edx/edx-django-utils/tree/master/edx_django_utils/monitoring/code_owner
