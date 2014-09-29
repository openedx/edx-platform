#########################
User API Module
#########################

.. module:: mobile_api

This page describes how to use the mobile user API to:

* `Get User Details`_
* `Get a User's Course Enrollments`_

.. _Get User Details:

*******************
Get User Details
*******************

.. .. autoclass:: mobile_api.users.views.UserDetail
..    :members:

**Use Case**

Get information about the specified user and access other resources the user
has permissions for.

Users are redirected to this endpoint after logging in.

You can use the **course_enrollments** value in the response to get a list of
courses the user is enrolled in.

**Example request**:

``GET /api/mobile/v0.5/users/{username}``

**Response Values**

* id: The ID of the user.

* username: The username of the currently logged in user.

* email: The email address of the currently logged in user.

* name: The full name of the currently logged in user.

* course_enrollments: The URI to list the courses the currently logged in user
  is enrolled in.

**Example response**

.. code-block:: json

    HTTP 200 OK  
    Vary: Accept   
    Content-Type: text/html; charset=utf-8   
    Allow: GET, HEAD, OPTIONS 

    {
        "id": 67, 
        "username": "mtwain", 
        "email": "mtwain@email-domain.com", 
        "name": "mtwain", 
        "course_enrollments": "http://localhost:8000/api/mobile/v0.5/users/mtwain/course_enrollments/"
    }

.. _Get a User's Course Enrollments:

**************************************
Get a User's Course Enrollments
**************************************

.. .. autoclass:: users.views.UserCourseEnrollmentsList
..    :members:

**Use Case**

Get information about the courses the currently logged in user is enrolled in.

**Example request**:

``GET /api/mobile/v0.5/users/{username}/course_enrollments/``

**Response Values**

* created: The date the course was created.
        
* mode: The type of certificate registration for this course:  honor or
  certified.
        
* is_active: Whether the course is currently active; true or false.
    
* course: A collection of data about the course:
        
* course_about: The URI to get the data for the course About page.
          
* course_updates: The URI to get data for course updates.
          
* number: The course number.
          
* org: The organization that created the course.
          
* video_outline: The URI to get the list of all vides the user can access in
  the course.
          
* id: The unique ID of the course.
          
* latest_updates:  Reserved for future use.
          
* end: The end date of the course.
          
* name: The name of the course.
          
* course_handouts: The URI to get data for course handouts.
          
* start: The data and time the course starts.
          
* course_image: The path to the course image.

**Example response**

.. code-block:: json

    HTTP 200 OK  
    Vary: Accept   
    Content-Type: text/html; charset=utf-8   
    Allow: GET, HEAD, OPTIONS 

    {
        "created": "2014-04-18T13:44:25Z", 
        "mode": "honor", 
        "is_active": true, 
        "course": {
            "course_about": "http://localhost:8000/api/mobile/v0.5/course_info/edX/Open_DemoX/edx_demo_course/about", 
            "course_updates": "http://localhost:8000/api/mobile/v0.5/course_info/edX/Open_DemoX/edx_demo_course/updates", 
            "number": "Open_DemoX", 
            "org": "edX", 
            "video_outline": "http://localhost:8000/api/mobile/v0.5/video_outlines/courses/edX/Open_DemoX/edx_demo_course", 
            "id": "edX/Open_DemoX/edx_demo_course", 
            "latest_updates": {
                "video": null
            }, 
            "end": null, 
            "name": "edX Demonstration Course", 
            "course_handouts": "http://localhost:8000/api/mobile/v0.5/course_info/edX/Open_DemoX/edx_demo_course/handouts", 
            "start": "1970-01-01T05:00:00Z", 
            "course_image": "/c4x/edX/Open_DemoX/asset/images_course_image.jpg"
        }
    }, 
    {
        "created": "2014-09-29T13:46:06Z", 
        "mode": "honor", 
        "is_active": true, 
        "course": {
            "course_about": "http://localhost:8000/api/mobile/v0.5/course_info/edX/DemoX/Demo_Course/about", 
            "course_updates": "http://localhost:8000/api/mobile/v0.5/course_info/edX/DemoX/Demo_Course/updates", 
            "number": "DemoX", 
            "org": "edX", 
            "video_outline": "http://localhost:8000/api/mobile/v0.5/video_outlines/courses/edX/DemoX/Demo_Course", 
            "id": "edX/DemoX/Demo_Course", 
            "latest_updates": {
                "video": null
            }, 
            "end": null, 
            "name": "edX Demonstration Course", 
            "course_handouts": "http://localhost:8000/api/mobile/v0.5/course_info/edX/DemoX/Demo_Course/handouts", 
            "start": "2013-02-05T05:00:00Z", 
            "course_image": "/c4x/edX/DemoX/asset/images_course_image.jpg"
        }
    }