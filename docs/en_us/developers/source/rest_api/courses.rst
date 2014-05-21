###############################
ReST API for Courses
###############################

The edX ReST API for courses enables you to:

* `Get a List of Courses`_
* `Get Course Details`_


.. _Get a List of Courses:

**********************
Get a List of Courses
**********************

.. http:get:: /api/courses

  Retrieves a list of courses in the edX Platform as a JSON representation (array) of the set of Course entities.

   **Example request**:

   .. sourcecode:: http

      GET /api/courses

   **Example response**:

   .. sourcecode:: http

      HTTP 200 OK
      Vary: Accept
      Content-Type: text/html; charset=utf-8
      Allow: GET, HEAD, OPTIONS

      [
          {
              "category": "course", 
              "name": "edX Demonstration Course", 
              "uri": "http://localhost:8000/api/courses/edX/Open_DemoX/edx_demo_course", 
              "number": "Open_DemoX", 
              "due": null, 
              "org": "edX", 
              "id": "edX/Open_DemoX/edx_demo_course"
          }
          {
              "category": "course", 
              "name": "Introduction to Computer Science", 
              "uri": "http://localhost:8000/api/courses/University/101/1_2014", 
              "number": "101", 
              "due": null, 
              "org": "edX University", 
              "id": "University/101/1_2014"
          }
      ]

.. _Get Course Details:

**********************
Get Course Details
**********************

.. http:get:: /api/courses/{course ID}

  Retrieves a list of courses in the edX Platform as a JSON representation (array) of the set of Course entities.

   **Example request**:

   .. sourcecode:: http

      GET /api/courses

   **Example response**:

   .. sourcecode:: http

      HTTP 200 OK
      Vary: Accept
      Content-Type: text/html; charset=utf-8
      Allow: GET, HEAD, OPTIONS

      [
          {
              "category": "course", 
              "name": "edX Demonstration Course", 
              "uri": "http://localhost:8000/api/courses/edX/Open_DemoX/edx_demo_course", 
              "number": "Open_DemoX", 
              "due": null, 
              "org": "edX", 
              "id": "edX/Open_DemoX/edx_demo_course"
          }
          {
              "category": "course", 
              "name": "Introduction to Computer Science", 
              "uri": "http://localhost:8000/api/courses/University/101/1_2014", 
              "number": "101", 
              "due": null, 
              "org": "edX University", 
              "id": "University/101/1_2014"
          }
      ]