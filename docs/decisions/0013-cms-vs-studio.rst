Terminology: CMS vs Studio
==========================

Synopsis
--------

There has been disagreement over whether Open edX's content authoring Web service is called "CMS" or "Studio".

This ADR decides that:

* "CMS" is the proper name of the Web service.
* "Studio" is the content authoring product that CMS powers.

Status
------

Accepted


Context
-------

edx-platform contains two semi-coupled Django projects. Although the projects share a lot of code and data, they have two different Django entry points and are generally deployed as distinct Web services.

The Django project defined under the ``./lms`` directory has many responsibilities, but its cardinal role is to host the instructor- and learner-facing learning experience. The Web service deployed from it is consistently referred to as "LMS" (for Learning Management System).

The Django project defined under the ``./cms`` directory is responsible for authoring, versioning, and publishing learning content to LMS. The Web service deployed from it was originally named "CMS" (for Content Management System). The primary user-facing Web application that it powers is named "Studio". Other applications include LabXChange, which uses the service's APIs to power content authoring capabilities.

In the past, there had been a push to update code references from "CMS" to "Studio", in an effort to (a) match the Studio product and (b) disambiguate the service from the Drupal CMS, which was being used internally to manage edX's marketing site. However, this effort was never fully followed through upon, and both names for the service can be found throughout code old and new, with different Open edX community members expressing preferences for one name or the other.


Let's choose one name for the Web service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Having two names for the same thing is annoying, especially when that thing is a core component of a software ecosystem. Whenever a developer needs to reference CMS/Studio, either in code or in documentation, they must arbitrarily choose one name or the other. Often, they will have to justify why they chose one name over the other to reviewers, who may have mixed opinions on which name to use. This is a waste of time, and the end result is that our code is more confusing and less predictable.

Arguments in favor of "Studio"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The environment variable used to specify CMS/Studio's configuration YAML path is ``STUDIO_CFG``.
* In both the old Ansible installation pathway and in Tutor, the default CMS/Studio domain is ``studio.<BASE_DOMAIN>``.
* Devstack calls the CMS/Studio docker-compose service ``studio``.
* It may be good for the Web service and the primary product it supports (Studio) to have the same name.
* Words (eg "Studio") are more accessible to new community members than initialisms (eg "CMS") are.
* "CMS" is a generic term for software that creates and edits digital content (see: Wordpress, Wagtail, et al), and thus may be ambiguous as a name for the content authoring service.
* When reading code, ``studio`` is more visually distinct from ``lms`` than ``cms`` is.

Arguments in favor of "CMS"
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* The directory itself is named ``./cms``, and top-level code directories are difficult to rename.
* All Django management commands against CMS/Studio are invoked as ``./manage.py cms ...``, which would also be hard to change.
* Tutor, the supported community installation, consistently calls the Web service "CMS" in its documentation and setting names.
* The old Ansible installation pathway (which is still in use at edX.org) consistently uses ``cms``.
* The CMS/Studio service supports at least one major product other than Studio: LabXChange. Thus, it may be worthwhile differentiating the Web service from its main product, allowing each to evolve separately without generating future terminology confusion.
* Parts of the Studio interface are being reimplemented as micro-frontends, which are presented as being part of the "Studio" product but are hosted separately from the CMS/Studio Web service.
* Although "CMS" is an ambiguous term outside of the context of Open edX, within the context of edx-platform it is clear what "CMS" refers to.

Decision
--------

We will call the Web service "CMS". Going forward, "Studio" should only be used to refer to the user-facing content authoring product powered by CMS. The primary factor behind this decision was an understanding that it would be significantly easier to change references of "Studio" to "CMS" than it would be to go the opposite direction.


Consequences
------------

1. Immediately, the environment variable used to specify CMS/Studio's configuration YAML path will be changed to ``CMS_CFG``, allowing ``STUDIO_CFG`` to be used as a deprecated fallback. The ``STUDIO_CFG`` variable will be supported until at least the "O" named release.
2. An issue to switch from ``STUDIO_CFG`` to ``CMS_CFG`` will be filed with the Tutor project.
3. In devstack, the ``studio`` service will be renamed to ``cms``. An `issue to complete this work <https://github.com/openedx/devstack/issues/877>`_ has been filed in the devstack repository.
4. We will circulate this ADR via the Open edX Slack and forum, encouraging others to reference it to help settle any CMS vs. Studio terminology disagreements going forward.
