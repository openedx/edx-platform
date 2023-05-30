Options for Extending the edX Platform
--------------------------------------

Open edX platform development aims to follow the `Open-Closed Principle`_: developers should be able to extend the platform to suit their needs ("open") without relying upon the details of the platform's internal implementation ("closed"). This makes it easier to maintain and refactor the platform's core, while enabling experimentation and volitility in its extensions.

There are many different ways to integrate with Open edX. If you would like to build a feature or integration that does **not** seem to be supported by these integration methods, consider proposing a new extension point in the core that would make possible the functionality you have in mind. When you submit a pull request for a new extension point, be sure to include a change to this file to document your new extension point. (Doing so will also notify reviewers that want to help with making the platform more extensible.)

Throughout this document, we will refer to the **Status** of each specific extension point:

* ✅ **Stable**: We actively recommend that developers use these. Core developers strive to avoid breaking these type extensions. When breaking changes are necessary, they will go through the `standard deprecation process <https://open-edx-proposals.readthedocs.io/en/latest/processes/oep-0021-proc-deprecation.html>`_.
* ⚠️ **Provisional**: We cautiously recommend these for use when Stable extension points are not sufficient. They may or may not be as well-documented. Core deevlopers may need to introduce breaking changes from time to time, but will ensure that these changes are communicated via the deprecation process, the named release notes, or both.
* 🕰️ **Legacy**: We preserve these for backwards compatibility with existing extensions, but not recommended for newer projects. In the future, they may be deprecated, with ample notice and migration recommendations.
* ❌ **Discouraged**: We do not encourage or support these. Core platform changes may break these extensions at any time. New extensions should avoid them, and existing extensions should migrate off of them.


.. _Open-Closed Principle: https://en.wikipedia.org/wiki/Open%E2%80%93closed_principle

.. contents:: **Integration Methods Overview**


REST API Integration with External Applications
===============================================

⚠️ **Provisional**

The Open edX platform provides a suite of REST APIs that any type of external application can use. Auto-generated API documentation for the main LMS and Studio APIs is available at (LMS URL)/api-docs/ and (Studio URL)/api-docs/ .

Things that you can develop as an external application using REST APIs include:

* Marketing sites / course catalogs
* Custom learning frontends
* Native mobile applications
* E-commerce and subscription management portals
* Administration tools
* Custom course authoring tools

You can write your external application using any language and framework you'd like. The API specifications are available in OpenAPI format (e.g. at /api-docs/?format=openapi), and you can use the `OpenAPI Generator`_ to generate an API client library in the language of your choice.

Be aware that most existing REST APIs are not considered stable, and some platform features lack a REST API. We welcome help as we work to standardize our API practices and version them to create API stability.

.. _OpenAPI Generator: https://github.com/OpenAPITools/openapi-generator

Content Integrations
====================

If you want to provide learners with new content experiences within courses, options include:

.. list-table::
   :header-rows: 1
   :widths: 15 10 75

   * - Type
     - Status
     - Details
   * - **XBlocks**
     - ✅ **Stable**
     - XBlocks are python plugins specific to Open edX that get installed into edx-platform and can be used to build courses. An XBlock defines a new *type* of interactive component, and authors can then create many instances of that content type in their courses (each with different settings and content). If you only need to support Open edX, XBlocks provide the best user experience. Open edX operators must install an XBlock into their Open edX instance before it can be used. See the `XBlock tutorial`_ to learn more about XBlocks.
   * - **LTI**
     - ✅ **Stable**
     - Learning Tools Interoperability is a standard that allows an individual piece of learnable/interactive content (the "tool") to be embedded via an IFrame in a host Learning Platform (the "consumer") such as Open edX. Open edX supports LTI content in both directions: `as a consumer`_ (external content appearing in an Open edX course) and `as a provider`_ (Open edX course content appearing in an external Learning Platform). If you need to support multiple Learning Platforms, and not just Open edX, LTI is usually the best way to integrate your content. Note that not all LTI versions/features are supported, however.
   * - **Custom JavaScript Applications**
     - ✅ **Stable**
     - If you have a single piece of content, such as a single interactive HTML5 animation or problem, and you want to use it in an Open edX course, you can create it as a `custom JavaScript application`_. Unlike XBlocks, these applications can be implemented without intervention by the Open edX operator.
   * - **External Graders**
     - 🕰️ **Legacy**
     - An external grader is a service that receives learner responses to a problem, processes those responses, and returns feedback and a problem grade to the edX platform. You build and deploy an external grader separately from the edX platform. An external grader is particularly useful for software programming courses where learners are asked to submit complex code. See the `external grader documentation`_ for details.
   * - **TinyMCE (Visual Text/HTML Editor) Plugins**
     - ⚠️ **Provisional**
     - TinyMCE's functionality can be extended with so-called Plugins. Custom TinyMCE plugins can be particularly useful for serving certain content in courses that isn't available yet; they can also be used to facilitate the educator's work. `You can follow this guide to install and enable custom TinyMCE plugins`_.

For a more detailed comparison of content integration options, see `Options for Extending the edX Platform`_ in the *Open edX Developer's Guide*.

.. _XBlock tutorial: https://edx.readthedocs.io/projects/xblock-tutorial/en/latest/
.. _as a consumer: https://edx.readthedocs.io/projects/edx-partner-course-staff/en/latest/exercises_tools/lti_component.html
.. _as a provider: https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/lti/
.. _Options for Extending the edX Platform: https://edx.readthedocs.io/projects/edx-developer-guide/en/latest/extending_platform/extending.html
.. _custom JavaScript application: https://edx.readthedocs.io/projects/edx-developer-guide/en/latest/extending_platform/javascript.html
.. _external grader documentation: https://edx.readthedocs.io/projects/open-edx-ca/en/latest/exercises_tools/external_graders.html
.. _You can follow this guide to install and enable custom TinyMCE plugins: extensions/tinymce_plugins.rst

Platform Features (Integrating Python Code)
===========================================

If you wish to customize aspects of the learner or educator experiences, you'll most likely need to create a Python plugin that can be installed into the platform and which uses Python APIs to extend the platform's functionality.

Most python plugins are enabled using one of two methods:

1. A Python Entry point: the core Open edX platform provides a standard plugin loading mechanism in |edx_django_utils.plugins|_ which uses `stevedore`_ to find all installed python packages that declare a specific "entry point" in their setup.py file. See the ``entry_points`` defined in edx-platform's own ``setup.py`` for examples.
2. A Django setting: Some plugins require modification of Django settings, which is typically done by editing ``/edx/etc/lms.yml`` (in Production) or ``edx-platform/lms/envs/private.py`` (on Devstack).

.. |edx_django_utils.plugins| replace:: ``edx_django_utils.plugins``
.. _edx_django_utils.plugins: https://github.com/openedx/edx-django-utils/blob/master/edx_django_utils/plugins
.. _stevedore: https://pypi.org/project/stevedore/

Here are the different integration points that python plugins can use:

.. list-table::
   :header-rows: 1
   :widths: 15 10 75

   * - Plugin Type
       (and entry point or setting)
     - Status
     - Details
   * - Django App Plugin (``lms.djangoapp`` and ``cms.djangoapp``)
     - ⚠️ **Provisional**
     - A "Django app plugin" is a self-contained Django `Application`_ that can define models (MySQL tables), new REST APIs, signal listeners, asynchronous tasks, and more. Even some parts of the core platform are implemented as Django app plugins, for better separation of concerns (``announcements``, ``credentials``, ``grades``, etc.) Read the `Django app plugin documentation`_ to learn more.

       Plugins can also inject custom data into django template contexts, to affect standard pages delivered by the core platform. See `Plugin Contexts`_ to learn more.
   * - Course tab (``openedx.course_tab``)
     - 🕰️ **Legacy**
     - A course tab plugin adds a new tab shown to learners within a course. ``courseware``, ``course_info``, and ``discussion`` are examples of built-in tab plugins. Read the `course tabs documentation`_ to learn more.

       This API may be changing soon with the new Courseware microfrontend implementation.
   * - Course tool (``openedx.course_tool``)
     - 🕰️ **Legacy**
     - The course home page (the landing page for the course) includes a "Course Tools" section that provides links to "tools" associated with the course. Examples of course tool plugins included in the core are reviews, updates, and bookmarks. See |course_tools.py|_ to learn more.

       This API may be changing soon with the new Courseware microfrontend implementation.
   * - Custom registration form app (``REGISTRATION_EXTENSION_FORM`` Django setting in the LMS)
     - ⚠️ **Provisional**
     - By default, the registration page for each instance of Open edX has fields that ask for information such as a user’s name, country, and highest level of education completed. You can add custom fields to the registration page for your own Open edX instance. These fields can be different types, including text entry fields and drop-down lists. See `Adding Custom Fields to the Registration Page`_.
   * - Learning Context (``openedx.learning_context``)
     - ⚠️ **Provisional**
     - A "Learning Context" is a course, a library, a program, a blog, an external site, or some other collection of content where learning happens. If you are trying to build a totally new learning experience that's not a type of course, you may need to implement a new learning context. Learning contexts are a new abstraction and are only supported in the nascent Learning-Core-based XBlock runtime. Since existing courses use modulestore instead of Learning Core, they are not yet implemented as learning contexts. However, Learning-Core-based content libraries are. See |learning_context.py|_ to learn more.
   * - User partition scheme (``openedx.user_partition_scheme`` and ``openedx.dynamic_partition_generator``)
     - ⚠️ **Provisional**
     - A user partition scheme is a named way for dividing users in a course into groups, usually to show different content to different users or to run experiments. Partitions may be added to a course manually, or automatically added by a "dynamic partition generator." The core platform includes partition scheme plugins like ``random``, ``cohort``, and ``enrollment_track``. See the |UserPartition docstring|_ to learn more.
   * - XBlock (``xblock.v1``)
     - ✅ **Stable**
     - An XBlock provides a new type of learnable content that can be used in courses, content libraries, etc. See `Content Integrations`_.
   * - XBlock unit tests (``xblock.test.v0``)
     - ⚠️ **Provisional**
     - XBlocks can also install test code that will then be run alongside the platform's usual python unit tests. It's unclear how well-supported this is at the moment.
   * - Pluggable override (``edx_django_utils.plugins.pluggable_override.pluggable_override``)
     - ⚠️ **Provisional**
     - This decorator allows overriding any function or method by pointing to an alternative implementation in settings. Read the |pluggable_override docstring|_ to learn more.
   * - Open edX Events
     - ✅ **Stable**
     - Events are part of the greater Hooks Extension Framework for open extension of edx-platform. Events are a stable way for plugin developers to react to learner or author events. They are defined by a `separate events library`_ that developers can include in their requirements to develop and test the code without creating a dependency on this large repo. For more information see the `hooks guide`_.
   * - Open edX Filters
     - ✅ **Stable**
     - Filters are also part of Hooks Extension Framework for open extension of edx-platform. Filters are a flexible way for plugin developers to modify learner or author application flows. They are defined by a `separate filters library`_ that developers can include in their requirements to develop and test the code without creating a dependency on this large repo. For more information see the `hooks guide`_.

Methods for integration Python code that are ❌ **Discouraged**
**************************************************************

In any of the Python integrations listed above, it is technically possible to import and reference code from the core edx-platform repository. Several existing plugins use this pattern::

  try:
      from lms import some_module
  except ImportError:
      # In unit tests, edx-platform isn't available, so all code used
      # by tests must handle this case. Alternatively, some plugins
      # clone the entirety of edx-platform into their repository,
      # making it so the try-catch isn't necessary.
      some_module = None

Despite its current usage, this pattern is discouraged. *Why?*

* **Upstream changes may fail silently**. Imagine that upstream developers, unaware of this plugin, rename ``some_module`` to ``some_module_improved``. This would cause the import to silently fail, causing ``some_module`` to be set to ``None``, causing leading to bugs or confusing errors elsewhere in the program's logic.
* **It makes the core platform harder to maintain**. As mentioned in the previous point, plugins using this pattern make it harder for core developers to maintain and refactor edx-platform, as any core change has the potential to break such plugins.
* **It creates bidirectional dependency**. Core edx-platform code depends on a handful of plugins. This "Core imports" pattern causes the plugin to also depend on core edx-platform code, forming a circular dependency. In general, circular dependencies make code harder to test, refactor, package, and reason about.
* **It avoids usage of better extension points**. This extension points listed in this document as Stable and Provisional do not suffer any of the drawbacks above. However, their learning curves may seem slightly steeper, since any extension point is by nature more abstract than a direct code import. That said, even if core imports are easier to use in the short term, they take time away from extension developers & core maintainers that could be used to learn, document, and improve the Stable and Provisional extension points.

.. _Application: https://docs.djangoproject.com/en/3.0/ref/applications/
.. _Django app plugin documentation: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
.. _Plugin Contexts: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/plugins/docs/decisions/0003-plugin-contexts.rst
.. _course tabs documentation: https://openedx.atlassian.net/wiki/spaces/AC/pages/30965919/Adding+a+new+course+tab
.. |course_tools.py| replace:: ``course_tools.py``
.. _course_tools.py: https://github.com/openedx/edx-platform/blob/master/openedx/features/course_experience/course_tools.py
.. _Adding Custom Fields to the Registration Page: https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/customize_registration_page.html
.. |learning_context.py| replace:: ``learning_context.py``
.. _learning_context.py: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/xblock/learning_context/learning_context.py
.. |UserPartition docstring| replace:: ``UserPartition`` docstring
.. _UserPartition docstring: https://github.com/openedx/edx-platform/blob/f8cc58618a39c9f7b8e9e1001eb2d7a10395797e/common/lib/xmodule/xmodule/partitions/partitions.py#L105-L120
.. |pluggable_override docstring| replace:: ``pluggable_override`` docstring
.. _pluggable_override docstring: https://github.com/openedx/edx-django-utils/blob/master/edx_django_utils/plugins/pluggable_override.py
.. _separate events library: https://github.com/eduNEXT/openedx-events/
.. _separate filters library: https://github.com/eduNEXT/openedx-filters/
.. _hooks guide: https://github.com/openedx/edx-platform/blob/master/docs/guides/hooks/index.rst

Platform Look & Feel
====================

Themes ("Comprehensive Theming")
********************************

🕰️ **Legacy**

Changing the look and feel of the edX platform is generally done by creating a new "theme". See `Changing Themes for an Open edX Site`_ for documentation. Note that most theming documentation applies to the legacy UI components used in edX, which are .html files (django/mako templates) rendered by the backend and styled using either the "v1" or "v2" (a.k.a. "Pattern Library") stylesheets. However, the platform UI is slowly being replaced by new React-based "MicroFrontEnds" (MFEs), and a different approach is required for theming MFEs (see `Theming Microfrontends`_).

Theming Microfrontends
**********************

⚠️ **Provisional**

Methods for theming MFEs are still being developed. It is likely to involve:

#. Branding: modifying fonts, colors, and logos via themes/css (there is an |example edx theme|_ that you can use as a template for defining fonts and colors, but some MFEs currently lack a mechanism for changing the theme).
#. Configuration: modifying settings and toggles via MFE configuration settings
#. Customization: gives the ability to override specific elements like the header and footer to better reflect your branding or offer different functionality - see `Overriding Brand Specific Elements`_.
#. Frontend Plugins: runtime configuration of frontend components in designated slots on frontend pages

In addition, Open edX operators will be able to replace entire MFEs with completely custom MFE implementations that use the same backend APIs.

.. |example edx theme| replace:: example ``edx`` theme
.. _example edx theme: https://github.com/openedx/paragon/tree/master/scss/edx
.. _Changing Themes for an Open edX Site: https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/changing_appearance/theming/
.. _Overriding Brand Specific Elements: https://edx.readthedocs.io/projects/edx-developer-docs/en/latest/developers_guide/micro_frontends_in_open_edx.html#overriding-brand-specific-elements

Custom frontends
****************

⚠️ **Provisional**

If you need a *very* custom look and feel for your users, and you have the time and resources required for a huge project, you can consider creating a custom frontend for Open edX, which is a completely separate application that runs on its own domain and integrates with Open edX using REST APIs. The edX Mobile App can be thought of as an example of a separate frontend that connects to Open edX using only REST APIs. Another example is `LabXchange <https://www.labxchange.org/>`_. If you develop your custom frontend using Django, you may wish to use the `auth-backends <https://github.com/openedx/auth-backends>`_ django plugin for user authentication.
