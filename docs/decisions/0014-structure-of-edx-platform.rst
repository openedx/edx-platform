The Stucture of the edx-platform Repository
-------------------------------------------


Status
======

Draft


Context
=======

Glossary
********

* **Python module:** A file containing Python code, named with a ``.py`` suffix.`
* **Python package:** A directory (a.k.a. folder) containing Python modules.
* **Python project:** A directory containing a ``setup.py`` module and one or more Python package(s) and/or other module(s). A project can installed using ``pip``, either from a local directory or via the `Python Package Index (PyPI) https://pypi.org`. Often referred to as a "package" or "library".
* **Django project**: A directory containing settings and application code necessary to run a Django-based Web application. Typically, Django projects include a ``manage.py`` file; edx-platform's two Django projects share a single ``manage.py`` in the repository root.
* **Django app**: A Python package that forms a part of a Django project. Can include URL patterns, HTTP views, namespaced database models, and other Django resources and Python utilities.
* **static assets:** images, CSS files, JavaScript files, and other files needed to run or test edx-platform that are not Python modules.
* **tooling:** files in edx-platform that support its build, testing, or CI processes, but are not executed in production.
* **structure**: The layout of edx-platform, including the naming and directory placement of its project(s), packages, modules, static assets, and tooling, as well as the dependency relationship between those entities. (Note: In this ADR, we intentionally avoid delving into deeper interpretations of "code structure" such as object class hierarches, separation of bounded contexts, etc. While these are important structural considerations, they are beyond the scope of the surface-level refactorings recommended in this ADR.)

Motivation
**********

edx-platform is a large and complex repository.
It contains six Python projects and two Django projects, comprised of over X total lines of Python code (excluding comments and whitespace) added by at least Y different contributors over more than a decade of rapid development.
Although the repository's structure is not visible to the end user, it is daily consideration for edx-platform contributors, carrying the potential to assist, annoy, or even mislead.
By formalizing and proactively refactoring the structure of this repository, we aim to:

* lower the learning for new and experienced Open edX developers alike,
* increase decision-making velocity around refactoring and feature development, and
* communicate our medium- and long-term architectual goals to edx-platform contributors.

Current State
*************

.. list-table:: Current edx-platform Python package structures
   :header-rows: 1

   * - Directory
     - Apparent purpose
   * - ``./lms``
     - Root for the LMS Django project
   * - ``./lms/djangoapps``
     - Django applications used in the LMS.
   * - ``./lms/lib``
     - Additional Python pacakges used by LMS Django applications.
   * - ``./cms``
     - Root for the CMS Django project
   * - ``./cms/djangoapps``
     - Django applications used in the CMS.
   * - ``./cms/lib``
     - Additional Python pacakges used by CMS Django applications.
   * - ``./common/djangoapps``
     - Django applications used by both the LMS and CMS.
   * - ``./common/lib``
     - Home for Python projects used by both the LMS and CMS. Intended for extraction into separate repositories.o
   * - ``./openedx/``
     - A new root package for *all* edx-platform code, include code used in LMS, CMS, or both. At the time of creation, it was thought that `all Open edX repositories would create matching openedx root packages <https://github.com/openedx/edx-platform/pull/5942#issuecomment-66117744>`_, allowing all Open edX code to be imported like ``import openedx.foo.bar.baz``, much like Django core and extensions can be imported via ``import django.foo.bar.baz``. This never happened.
   * - ``./openedx/core/djangoapps``
     - Django applications forming the "core" edx-platform functionality.
   * - ``./openedx/core/djangolib``
     - Additional core Python packages that depend upon Django libraries. It was believed at one point tha Web-framework-agnostic core could exist in edx-platform, so there was an effort to isolate Django-dependent code from Django-independent code.
   * - ``./openedx/core/lib``
     - Additional core Python packages with no Django dependencies.
   * - ``./pavelib``
     - edx-platform tooling build on the "paver" framework. Not executed by the LMS or CMS applications in production.


Decision
========

TBD

.. list-table:: Target edx-platform package structures
   :header-rows: 1

   * - Directory
     - Purpose
   * - ``./lms``
     - Root for the LMS Django project
   * - ``./lms/apps``
     - Django applications used in the LMS (but not the CMS).
   * - ``./lms/lib``
     - Additional Python pacakges used by LMS Django applications.
   * - ``./cms``
     - Root for the CMS Django project
   * - ``./cms/apps``
     - Django applications used in the CMS (but not the LMS).
   * - ``./cms/lib``
     - Additional Python pacakges used by CMS Django applications.
   * - ``./common/apps``
     - Django applications used by both the LMS and CMS.
   * - ``./common/lib``
     - Additional Python pacakges used by both the LMS and CMS.
   * - ``./pavelib``
     - edx-platform tooling build on the "paver" framework. Not executed by the LMS or CMS applications in production.

Consequences
============

TBD


Alternatives Considered
=======================

TBD

