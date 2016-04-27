.. _EdX Platform Course Structure API Overview:

################################################
Course Structure API Overview
################################################

Use the edX Platform Course Structure API to view course details, including the
blocks in the course and the course grading policy.

.. contents::
   :local:
   :depth: 1

********************************************
Course Structure API Version 0
********************************************

The Course Structure API is currently at version 0. We plan on making
significant enhancements to this API. Currently the Course Structure API is for
internal use only; third parties cannot use the API to access course structure
data.

**********************************************
Course Structure API Resources and Endpoints
**********************************************

The Course Structure API supports the following resources, tasks, methods, and
endpoints.

.. list-table::
   :widths: 10 70
   :header-rows: 1

   * - To:
     - Use this endpoint:
   * - :ref:`Get a list of courses in the edX platform <Get a List of Courses>`
     - GET /api/course_structure/v0/courses/
   * - :ref:`Get details about a course <Get Course Details>`
     - GET /api/course_structure/v0/courses/{course_id}/
   * - :ref:`Get a course's structure, or blocks <Get the Course Structure>`
     - GET /api/course_structure/v0/course_structures/{course_id}/
   * - :ref:`Get a course's grading policy <Get the Course Grading Policy>`
     - GET /api/course_structure/v0/grading_policies/{course_id}/
