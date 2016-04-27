.. _Courses API Overview:

#############################
Courses Overview
#############################

Use the Courses API to obtain information about edX courses.



.. contents::
   :local:
   :depth: 1

*****************************************
Courses API Version and Status
*****************************************

The Courses API is currently at version 1.0. We plan to make
significant enhancements to this API.

*****************************
Courses API Endpoints
*****************************

The Courses API includes the **Courses** resource. This resource
supports the following tasks, methods, and endpoints.

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Task
     - Method
     - Endpoint
   * - :ref:`Get a list of all courses in a catalog <Get a List of All Courses
     in a Catalog>`
     - GET
     - /api/v1/catalogs/{id}/courses/
