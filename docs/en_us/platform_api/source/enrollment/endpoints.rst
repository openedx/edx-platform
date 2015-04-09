.. _edX Enrollment API Endpoints:

################################################
Enrollment API Endpoints
################################################

You use the Enrollment API to view information about users and
their course enrollments, course information, and videos and transcripts.

The following tasks and endpoints are currently supported. 


.. list-table::
   :widths: 10 70
   :header-rows: 1

   * - To:
     - Use this endpoint:
   * - :ref:`Get the user's enrollment status in a course <Get the Users Enrollment Status in a Course>`
     - /api/enrollment/v1/enrollment/{user_id},{course_id}
   * - :ref:`Get enrollment details for a course<Get Enrollment Details for a Course>`
     - /api/enrollment/v1/course/{course_id}
   * - :ref:`View a user's enrollments <View and add to a Users Course Enrollments>`
     - /api/enrollment/v1/enrollment
   * - :ref:`Enroll a user in a course <View and add to a Users Course Enrollments>`
     - /api/enrollment/v1/enrollment{“course_details”:{“course_id”:“*course_id*”}}