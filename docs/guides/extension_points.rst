Options for Extending the edX Platform
--------------------------------------

Open edX platform development follows the `Open-Closed Principle`_: we want Open edX to be an extensible platform that allows developers to build extensions that integrate with the core of the platform. This allows the core to remain small, while volatile extensions remain in the periphery.

As you can see in this document, there are many different ways to integrate with Open edX. However, we know that there are still some features/integrations that are not possible today without modifying the core. If you have such a need, please consider proposing a new extension point in the core that would make possible the functionality you have in mind. When submit a pull request for a new extension point, be sure to include a change to this file to document your new extension point. (Doing so will also notify reviewers that want to help with making the platform more extensible.)


.. _Open-Closed Principle: https://en.wikipedia.org/wiki/Open%E2%80%93closed_principle

.. contents:: **Integration Methods Overview**


REST API Integration with External Applications
===============================================

The Open edX platform provides a suite of REST APIs that any type of external application can use. Auto-generated API documentation for the main LMS and Studio APIs is available at (LMS URL)/api-docs/ and (Studio URL)/api-docs/ .

Things that you can develop as an external application using REST APIs include:

* Marketing sites / course catalogs
* Custom LMS frontends
* Native mobile applications
* E-commerce and subscription management portals
* Administration tools
* Custom course authoring tools

You can write your external application using any language and framework you'd like. The API specifications are available in OpenAPI format (e.g. at /api-docs/?format=openapi), and you can use the `OpenAPI Generator`_ to generate an API client library in the language of your choice.

.. _OpenAPI Generator: https://github.com/OpenAPITools/openapi-generator

Content Integrations
====================

If you want to provide learners with new content experiences within courses, options include:

* **XBlocks**: python plugins specific to Open edX that get installed into edx-platform and can be used to build courses. An XBlock defines a new *type* of interactive component, and authors can then create many instances of that content type in their courses (each with different settings and content). If you only need to support Open edX, XBlocks provide the best user experience. See the `XBlock tutorial`_ to learn more.
* **LTI**: Learning Tools Interoperability is a standard that allows an individual piece of learnable/interactive content (the "tool") to be embedded via an IFrame in a host LMS (the "consumer") such as the Open edX LMS. Open edX supports LTI content in both directions: `as a consumer`_ (external content appearing in an Open edX course) and `as a provider`_ (Open edX course content appearing in an external LMS). If you need to support multiple LMSs, and not just Open edX, LTI is usually the best way to integrate your content. Note that not all LTI versions/features are supported, however.
* **Custom JavaScript Applications**: If you have a single piece of content, such as a single interactive HTML5 animation or problem, and you want to use it in an Open edX course, you can create it as a `custom JavaScript application`_.
* **External Graders**: An external grader is a service that receives learner responses to a problem, processes those responses, and returns feedback and a problem grade to the edX platform. You build and deploy an external grader separately from the edX platform. An external grader is particularly useful for software programming courses where learners are asked to submit complex code. See the `external grader documentation`_ for details.

For a more detailed comparison of content integration options, see `Options for Extending the edX Platform`_ in the *Open edX Developer's Guide*.

.. _XBlock tutorial: https://edx.readthedocs.io/projects/xblock-tutorial/en/latest/
.. _as a consumer: https://edx.readthedocs.io/projects/edx-partner-course-staff/en/latest/exercises_tools/lti_component.html
.. _as a provider: https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/lti/
.. _Options for Extending the edX Platform: https://edx.readthedocs.io/projects/edx-developer-guide/en/latest/extending_platform/extending.html
.. _custom JavaScript application: https://edx.readthedocs.io/projects/edx-developer-guide/en/latest/extending_platform/javascript.html
.. _external grader documentation: https://edx.readthedocs.io/projects/open-edx-ca/en/latest/exercises_tools/external_graders.html




Platform Features (Integrating Python Code)
===========================================

If you wish to change the way the edx-platform works, you'll most likely need to create a Python plugin that can be installed into the platform and which uses Python APIs to extend the platform's functionality.

Most python plugins are enabled using one of two methods:

1. A Python Entry point: the core Open edX platform provides a standard plugin loading mechanism in |openedx.core.lib.plugins|_ which uses `stevedore`_ to find all installed python packages that declare a specific "entry point" in their setup.py file. See the ``entry_points`` defined in edx-platform's own ``setup.py`` for examples.
2. A Django setting: Some plugins require modification of Django settings, which is typically done by editing ``/edx/etc/lms.yml`` (in Production) or ``edx-platform/lms/envs/private.py`` (on Devstack).

.. |openedx.core.lib.plugins| replace:: ``openedx.core.lib.plugins``
.. _openedx.core.lib.plugins: https://github.com/edx/edx-platform/blob/master/openedx/core/lib/plugins.py
.. _stevedore: https://pypi.org/project/stevedore/

Here are the different integration points that python plugins can use:

+---------------------+------------------------------------------+-------------------------------------------------------------+
| Plugin Type         | Entry point or setting                   | Details                                                     |
+=====================+==========================================+=============================================================+
| Django App Plugin   | ``lms.djangoapp`` and ``cms.djangoapp``  | A "Django app plugin" is a self-contained Django            |
|                     |                                          | `Application`_ that can define models (MySQL tables), new   |
|                     |                                          | REST APIs, signal listeners, asynchronous tasks, and more.  |
|                     |                                          | Even some parts of the core platform are implemented as     |
|                     |                                          | Django app plugins, for better separation of concerns       |
|                     |                                          | (``announcements``, ``credentials``, ``grades``, etc.)      |
|                     |                                          | Read the `Django app plugin documentation`_ to learn more.  |
|                     |                                          |                                                             |
|                     |                                          | Plugins can also inject custom data into django template    |
|                     |                                          | contexts, to affect standard pages delivered by the core    |
|                     |                                          | platform. See `Plugin Contexts`_ to learn more.             |
+---------------------+------------------------------------------+-------------------------------------------------------------+
| Course tab          | ``openedx.course_tab``                   | A course tab plugin adds a new tab shown to learners within |
|                     |                                          | a course. ``courseware``, ``course_info``, and              |
|                     |                                          | ``discussion`` are examples of built-in tab plugins.        |
|                     |                                          | Read the `course tabs documentation`_ to learn more.        |
+---------------------+------------------------------------------+-------------------------------------------------------------+
| Course tool         | ``openedx.course_tool``                  | The course home page (the landing page for the course)      |
|                     |                                          | includes a "Course Tools" section that provides links to    |
|                     |                                          | "tools" associated with the course. Examples of course tool |
|                     |                                          | plugins included in the core are reviews, updates, and      |
|                     |                                          | bookmarks. See |course_tools.py|_ to learn more.            |
+---------------------+------------------------------------------+-------------------------------------------------------------+
| Custom registration | ``REGISTRATION_EXTENSION_FORM`` Django   | By default, the registration page for each instance of Open |
| form app            | setting (LMS).                           | edX has fields that ask for information such as a user’s    |
|                     |                                          | name, country, and highest level of education completed.    |
|                     |                                          | You can add custom fields to the registration page for your |
|                     |                                          | own Open edX instance. These fields can be different types, |
|                     |                                          | including text entry fields and drop-down lists. See        |
|                     |                                          | `Adding Custom Fields to the Registration Page`_.           |
+---------------------+------------------------------------------+-------------------------------------------------------------+
| Learning Context    | ``openedx.learning_context``             | A "Learning Context" is a course, a library, a program, a   |
|                     |                                          | blog, an external site, or some other collection of content |
|                     |                                          | where learning happens. If you are trying to build a        |
|                     |                                          | totally new learning experience that's not a type of course,|
|                     |                                          | you may need to implement a new learning context.           |
|                     |                                          | Learning contexts are a new abstraction and are only        |
|                     |                                          | supported in the nascent Blockstore-based XBlock runtime.   |
|                     |                                          | Since existing courses use modulestore instead of           |
|                     |                                          | Blockstore, they are not yet implemented as learning        |
|                     |                                          | contexts. However, Blockstore-based content libraries are.  |
|                     |                                          | See |learning_context.py|_ to learn more.                   |
+---------------------+------------------------------------------+-------------------------------------------------------------+
| User partition      | ``openedx.user_partition_scheme`` and    | A user partition scheme is a named way for dividing users   |
| scheme              | ``openedx.dynamic_partition_generator``  | in a course into groups, usually to show different content  |
|                     |                                          | to different users or to run experiments. Partitions may be |
|                     |                                          | added to a course manually, or automatically added by a     |
|                     |                                          | "dynamic partition generator." The core platform includes   |
|                     |                                          | partition scheme plugins like ``random``, ``cohort``,       |
|                     |                                          | and ``enrollment_track``. See the |UserPartition docstring|_|
|                     |                                          | to learn more.                                              |
+---------------------+------------------------------------------+-------------------------------------------------------------+
| XBlock              | ``xblock.v1``                            | An XBlock provides a new type of learnable content that can |
|                     |                                          | be used in courses, content libraries, etc. See "Content    |
|                     |                                          | Integrations" above.                                        |
+---------------------+------------------------------------------+-------------------------------------------------------------+
| XBlock unit tests   | ``xblock.test.v0``                       | XBlocks can also install test code that will then be run    |
|                     |                                          | alongside the platform's usual python unit tests. It's      |
|                     |                                          | unclear how well-supported this is at the moment.           |
+---------------------+------------------------------------------+-------------------------------------------------------------+

.. _Application: https://docs.djangoproject.com/en/3.0/ref/applications/
.. _Django app plugin documentation: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
.. _Plugin Contexts: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/plugins/docs/decisions/0003-plugin-contexts.rst
.. _course tabs documentation: https://openedx.atlassian.net/wiki/spaces/AC/pages/30965919/Adding+a+new+course+tab
.. |course_tools.py| replace:: ``course_tools.py``
.. _course_tools.py: https://github.com/edx/edx-platform/blob/master/openedx/features/course_experience/course_tools.py
.. _Adding Custom Fields to the Registration Page: https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/customize_registration_page.html
.. |learning_context.py| replace:: ``learning_context.py``
.. _learning_context.py: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/xblock/learning_context/learning_context.py
.. |UserPartition docstring| replace:: ``UserPartition`` docstring
.. _UserPartition docstring: https://github.com/edx/edx-platform/blob/f8cc58618a39c9f7b8e9e1001eb2d7a10395797e/common/lib/xmodule/xmodule/partitions/partitions.py#L105-L120

Platform Look & Feel
====================

Themes ("Comprehensive Theming")
********************************

Changing the look and feel of the edX platform is generally done by creating a new "theme". See `Changing Themes for an Open edX Site`_ for documentation. Note that most theming documentation applies to the legacy UI components used in edX, which are .html files (django/mako templates) rendered by the backend and styled using either the "v1" or "v2" (a.k.a. "Pattern Library") stylesheets. However, the platform UI is slowly being replaced by new React-based "MicroFrontEnds" (MFEs), and a different approach is required for theming MFEs.

Theming Microfrontends
**********************
Methods for theming MFEs are still being developed. There is an |example edx theme|_ that you can use as a template for defining fonts and colors, but some MFEs currently lack a mechanism for changing the theme. You can also override specific elements like the header and footer to reflect your branding or offer different functionality - see `Overriding Brand Specific Elements`_.

.. |example edx theme| replace:: example ``edx`` theme
.. _example edx theme: https://github.com/edx/paragon/tree/master/scss/edx
.. _Changing Themes for an Open edX Site: https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/changing_appearance/theming/
.. _Overriding Brand Specific Elements: https://edx.readthedocs.io/projects/edx-developer-docs/en/latest/developers_guide/micro_frontends_in_open_edx.html#overriding-brand-specific-elements

Custom frontends
****************
If you need a *very* custom look and feel for your users, and you have the time and resources required for a huge project, you can consider creating a custom frontend for Open edX, which is a completely separate application that runs on its own domain and integrates with Open edX using REST APIs. The edX Mobile App can be thought of as an example of a separate frontend that connects to Open edX using only REST APIs. Another example is `LabXchange <https://www.labxchange.org/>`_. If you develop your custom frontend using Django, you may wish to use the `auth-backends <https://github.com/edx/auth-backends>`_ django plugin for user authentication.
