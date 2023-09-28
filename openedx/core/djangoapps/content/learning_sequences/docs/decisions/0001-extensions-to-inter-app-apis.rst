Extensions to Inter-app API Conventions
=======================================

Status
------

Draft


Context
-------

In order to improve the maintainability and stability of our applications, we
introduced ``edx-platform/docs/decisions/0002-inter-app-apis.rst``, which
outlines the use of package level ``api.py`` files to provide single-points of
entry to the app's functionality.

This ADR seeks to add further conventions to help address issues that have come
up in our usage over the years. Namely:

* It is difficult to determine exactly what is being returned by inter-app APIs.
* It is difficult to know exactly what valid inputs to inter-app APIs are.
* It is difficult to tell when we break compatibility in an inter-app API.
* Critical functionality (exercised via views) is sometimes missing from the
  inter-app API, or behaves differently from its REST counterpart.

If we find that this ADR's additional conventions are helpful, we can add them
to the existing set of Inter-app APIs defined at the top level of edx-platform.


Decision
--------

1. All API data structures will be declared as immutable attrs classes in a
   separate ``data.py`` file. All data class attributes will have type
   annotations.
2. Data structures in ``data.py`` will include basic validation of their inputs,
   though this will *not* include validation that requires database access.
3. All public inter-app API functions will use type annotations for arguments
   and return values.
4. All public inter-app API functions will be exported in the top level ``api``
   package. Other applications will only ever import from this top level
   package.
5. Views, tasks, and any other parts of the learning_sequences app that are not
   in the api package will obey the same rules that external apps would follow.
   This means that views for learning_sequences will only import from api and
   will not directly import from models.
6. Serializers for REST APIs will be defined as inner classes on the views.
   Serializer re-use across use cases will be explicitly discouraged to prevent
   modifications from rippling across and breaking compatibility elsewhere.
7. Wherever possible, API-level tests will be written without mocking internals,
   or prepping the database with model manipulations. The goal of this is to
   make it so that that API-level tests *only* break when there are in fact API
   changes. We can mock calls to other services, like grades.


Consequences
------------

1. It will be easier for other applications to access learning_sequence
   functionality in a more easily understood and maintainable way.
2. It will be easier to build and maintain plugin code that depends on this
   application.
3. Changes that break backwards compatibility will be more obvious.


References
----------

A lot of these extensions were either copied from or inspired by
`Django structure for scale and longevity <https://www.youtube.com/watch?v=yG3ZdxBb1oo>`_
presented by Radoslav Georgiev at EuroPython 2018, though there are a number of
differences like our use of ``attrs``, and trying to keep better backwards
compatibility with our existing ``api.py`` conventions.
