.. _Courses API Courses Resource:

########################################
Courses API Courses Resource
########################################

With the Courses API **Courses** resource, you can complete the
following tasks.

   * - :ref:`Get a list of all courses in a catalog <Get a List of All Courses
     in a Catalog>`
     - GET
     - /api/v1/catalogs/1/courses/

.. contents::
   :local:
   :depth: 1

.. _Get a List of All Courses in a Catalog:

**************************************
Get a List of All Courses in a Catalog
**************************************

The endpoint to get a list of all courses in a catalog is
``/api/v1/catalogs/{id}/courses/``.

=====================
Use Case
=====================

Get a list of all the active courses in a catalog. Active courses are courses
that are currently open for enrollment or that will open for enrollment in the
future.

=====================
Example Request
=====================

``GET /api/v1/catalogs/1/courses/``

=====================
Response Values
=====================

.. include:: ../shared/courses_response_values.rst

=====================================================
Example Response Showing a Catalog of Select Courses
=====================================================

.. include:: ../shared/courses_example_response.rst

