.. _EdX Platform Course Structure API Endpoints:

################################################
Course Structure API Endpoints
################################################

You use the Course Structure API to view information about
courses.

The following tasks and endpoints are currently supported. 


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
       