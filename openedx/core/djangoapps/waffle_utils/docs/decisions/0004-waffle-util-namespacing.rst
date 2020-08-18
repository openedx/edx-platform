Waffle Util Namespacing
***********************

Status
======

Draft

Context
=======

The toggle classes WaffleFlag and WaffleSwitch rely on several namespace classes (WaffleNamespace, WaffleSwitchNamespace, and WaffleFlagNamespace). In order to create a WaffleFlag (or WaffleSwitch), you must first create a Namespace object.

Other IDAs have active waffle flags and switches that don't use any namespacing, like this `example switch in ecommerce`_. Once WaffleFlag and WaffleSwitch are extracted to be used in other IDAs (see 0002-waffle-utils-extraction), the required namespace class will make this transition more difficult.

Additionally, the fully qualified waffle name, including the namespace, is required in code annotations and the django admin. Since it needs to be manually reconstructed by the developer, it has lead to copy/paste issues that are also difficult to lint.

Lastly, the namespace classes contain a lot of logic, but in effect, they only are used to ensure the flag name has a prefix like '<NAMESPACE_NAME>.<FLAG_NAME>'.

.. _example switch in ecommerce: https://github.com/edx/ecommerce/blob/e899c78325ac492d0a2b1ea0aab4d5e230262b8f/ecommerce/extensions/dashboard/users/views.py#L21

Decision
========

Change the interface to WaffleFlag and WaffleSwitch to simply take the complete flag name, rather than a Namespace object.

The constructor can assert that the name includes a `.` to help remind people to use some form of prefixed namespace.  However, an optional argument with a name like `skip_namespace_assertion=True` could be used to skip this assertion, enabling a simpler transition for existing flags and switches that don't meet this requirement.

Consequences
============

This change will enable WaffleFlag, WaffleSwitch, and all subclasses to have a simpler interface. In addition to a simpler constructor, we will no longer need to differentiate between an instance's namespaced and non-namespaced name.

.. note:: It would probably be simpler to make this change before these classes are extracted to ``edx-toggles``, so we have fewer places to update.

Implementation Steps:

* A rollout plan will be required to introduce this backward incompatible change. A possible plan might include the following:

  * This could include adding WaffleFlag2, WaffleSwitch2, CourseWaffleFlag2, etc. as new superclasses with the newer interface.
  * Once all known flags and switches have been updated, we can use the toggle state endpoint to see if there were any that were missed.
  * Once we are sure we know all usages of these classes, we can remove the old classes and rename the newer ones.
  * This change needs to be documented for the next Open edX release.
