.. _edX Enrollment API Overview:

################################################
Enrollment API Overview
################################################

Use the Enrollment API to view user and course enrollment
information and to enroll a user in a course.

.. contents::
   :local:
   :depth: 1

****************************************
Enrollment API Version and Status
****************************************

The Enrollment API is currently at version 1.0. We plan to make
significant enhancements to this API.

********************************************
Enrollment API Endpoints
********************************************

The Enrollment API supports the following tasks, methods, and endpoints.

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Task
     - Method
     - Endpoint
   * - :ref:`Get the user's enrollment status in a course <Get the Users Enrollment Status in a Course>`
     - GET
     - /api/enrollment/v1/enrollment/{user_id},{course_id}
   * - :ref:`Get the user's enrollment information for a course <Get Enrollment Details for a Course>`
     - GET
     - /api/enrollment/v1/course/{course_id}
   * - :ref:`View a user's enrollments <View and add to a Users Course Enrollments>`
     - GET
     - /api/enrollment/v1/enrollment
   * - :ref:`Enroll a user in a course <View and add to a Users Course Enrollments>`
     - POST
     - /api/enrollment/v1/enrollment{"course_details":{"course_id":"{course_id}"}}

