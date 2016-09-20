.. _Courses API Overview:

#############################
Courses API Overview
#############################

Use the Courses API to obtain information about edX courses.

.. contents::
   :local:
   :depth: 1

*****************************************
Courses API Version and Status
*****************************************

The Courses API is currently at version 1.0.

************************************
Courses API Resources and Endpoints
************************************

The Courses API includes the :ref:`Courses<Courses API Courses Resource>` and
:ref:`Blocks<Courses API Blocks Resource>` resources, and supports the following
tasks, methods, and endpoints.

=================
Courses Resource
=================

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Task
     - Method
     - Endpoint
   * - :ref:`Get a list of courses`
     - GET
     - /api/courses/v1/courses/
   * - :ref:`Get the details for a course`
     - GET
     - /api/courses/v1/courses/{course_key}/



=================
Blocks Resource
=================

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Task
     - Method
     - Endpoint

   * - :ref:`Get a list of the course blocks in a course`
     - GET
     - /api/courses/v1/blocks/ with required ``course_id`` parameter

   * - :ref:`Get a list of the course blocks in a block tree`
     - GET
     - /api/courses/v1/blocks/{usage_id}
