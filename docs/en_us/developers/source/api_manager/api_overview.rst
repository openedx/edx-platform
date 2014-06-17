###############################
edX ReST API Resources
###############################

**********
Courses
**********

.. list-table::
   :widths: 20 60
   :header-rows: 1

   * - Goal
     - Resource
   * - :ref:`Get a List of Courses`
     - GET /api/courses
   * - :ref:`Get Course Content`
     - GET /api/courses/{course_id}/content?type=content_type
   * - :ref:`Get Course Details`
     - GET /api/courses/{course_id}?depth=n
   * - :ref:`Get Content Details`
     - GET /api/courses/{course_id}/content/{content_id}?type=content_type
   * - :ref:`Get a Course Overview`
     - GET /api/courses/{course_id}/overview?parse=true
   * - :ref:`Get Course Updates`
     - GET /api/courses/{course_id}/updates?parse=true
   * - :ref:`Get Pages`
     - GET /api/courses/{course_id}/static_tabs?detail=true
   * - :ref:`Get Page Detail`
     - GET /api/courses/{course_id}/static_tabs/{tab_id}
   * - :ref:`Get Users in a Course`
     - GET /api/courses/{course_id}/users
   * - :ref:`Add a User to a Course`
     - POST /api/courses/{course_id}/users   
   * - :ref:`Get Details of a User in a Course`
     - POST /api/courses/{course_id}/users/{user_id} 
   * - :ref:`Unenroll a User from a Course`
     - DELETE /api/courses/{course_id}/users/{user_id} 
       
**********
Sessions
**********

.. list-table::
   :widths: 20 60
   :header-rows: 1

   * - Goal
     - Resource
   * - 
     - 