Inter-app APIs
--------------

Status
======

Accepted

Context
=======

The edx-platform Django project is a conglomeration of different LMS and Studio
features written in the structure of Django apps. Over the years, the boundaries
between features have become muddled for various reasons. We now find apps
intruding into the Python innards of other apps, making the intrusive apps
tightly dependent on the inner behaviors of other apps.

Due to this lack of clearly delimited separation of concerns, the monolith has
become hard to maneuver, comprehend, and modify.

Decisions
=========

1. Each Django app should clearly define a set of Python APIs that it exposes to
   other Django apps, which run within the LMS/Studio process.
2. Each app's Python APIs should be defined/exported in a Python module called
   "api.py", located in the top-most directory of the app.
3. The app's Python APIs should be well-named, self-consistent, and relevant to
   its own "domain" (without exposing technical and implementation details).
4. An app's Django models and other internal data structures should not be
   exposed via its Python APIs.
5. Ideally, tests should use only Python APIs declared in other apps' "api.py"
   files. However, if an app's API is needed only for testing (and not needed as
   part of the app's domain API), then test-relevant Python APIs should be
   defined/exported in an intentional Python module called "api_for_tests.py".

Exmaples
~~~~~~~~

As a reference example, see the Python APIs exposed by the grades app in the
`grades/api.py module`_.

.. _`grades/api.py module`: https://github.com/openedx/edx-platform/blob/master/lms/djangoapps/grades/api.py


Consequences
============

1. Explicitly defining Python APIs will prevent the proliferation of unintended
   entanglement between apps in the monolith.
2. When developers invest time in carefully considering Python APIs, they will
   need to consider good SOLID design practices for abstractions and
   encapsulation, leading to cleaner and more comprehensible code.
3. Python clients outside of an app will interface only through declared APIs in
   either "api.py" or "test_api.py" (or exported via an api/__init__.py). The
   provider app therefore has better control and oversight to support its
   intentional APIs.
