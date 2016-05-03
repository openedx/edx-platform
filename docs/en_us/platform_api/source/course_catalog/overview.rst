.. _Course Catalog API Overview:

#############################
Course Catalog API Overview
#############################

Use the Course Catalog API to obtain information about the catalogs that edX
offers, as well as information about the courses in a specific catalog.

.. contents::
   :local:
   :depth: 1

*****************************************
Course Catalog API Version and Status
*****************************************

The Course Catalog API is currently at version 1.0. We plan to make
significant enhancements to this API.

*****************************
Course Catalog API Endpoints
*****************************

The Course Catalog API includes the **Catalogs** resource. This resource
supports the following tasks, methods, and endpoints.

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Task
     - Method
     - Endpoint
   * - :ref:`Get a list of all available course catalogs <Get a List of All
     Course Catalogs>`
     - GET
     - /api/v1/catalogs/
   * - :ref:`Get information about a specific catalog <Get Information About a
     Specific Catalog>`
     - GET
     - /api/v1/catalogs/{id}/
   * - :ref:`Get a list of all courses in a catalog <Get a List of All Courses
     in a Catalog>`
     - GET
     - /api/v1/catalogs/{id}/courses/
