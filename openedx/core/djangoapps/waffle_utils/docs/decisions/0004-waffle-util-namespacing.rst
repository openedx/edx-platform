Waffle Util Namespacing
***********************

Status
======

Accepted

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

A possible rollout plan would be to introduce WaffleFlag and WaffleSwitch classes with the new interface when they are added into edx-toggles, and deprecate the old versions in edx-platform. This would enable us to reuse the same class names with a new import, for an iterative rollout.

Although it would be nice to update CourseWaffleFlag to have a similar interface for consistency, it is a lower priority if it is not moving to edx-toggles. See 0003-leave-course-waffle-flag.rst.

This change needs be documented for the next Open edX release.
