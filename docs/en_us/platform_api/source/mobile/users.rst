####################################
Mobile User API
####################################

This page describes how to use the Mobile User API to complete
these actions:

* `Get User Details`_
* `Get a User's Course Enrollments`_
* `Get or Change User Status in a Course`_

.. _Get User Details:

*******************
Get User Details
*******************

.. autoclass:: mobile_api.users.views.UserDetail

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

.. autoclass:: mobile_api.users.views.UserCourseEnrollmentsList

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

.. _Get or Change User Status in a Course:

**************************************
Get or Change User Status in a Course
**************************************

.. autoclass:: mobile_api.users.views.UserCourseStatus

**Example Response**

.. code-block:: json

    HTTP 200 OK  
    Vary: Accept   
    Content-Type: text/html; charset=utf-8   
    Allow: GET, HEAD, OPTIONS 

    {
        "last_visited_module_id": "i4x://edX/DemoX/html/6018785795994726950614ce7d0f38c5",  

        "last_visited_module_path": [
            "i4x://edX/DemoX/html/6018785795994726950614ce7d0f38c5", 
            "i4x://edX/DemoX/vertical/26d89b08f75d48829a63520ed8b0037d", 
            "i4x://edX/DemoX/sequential/dbe8fc027bcb4fe9afb744d2e8415855", 
            "i4x://edX/DemoX/chapter/social_integration", 
            "i4x://edX/DemoX/course/Demo_Course"
        ]
    }