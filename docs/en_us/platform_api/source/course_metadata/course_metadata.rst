########################################
Course Metadata API Module
########################################

This page contains information on using the Course Metadata API to
complete these actions:


.. 

**************************
Get a List of Courses
**************************

.. autoclass:: course_metadata_api.v0.views.CourseList

**Example response**

.. code-block:: json

    {
        "count": 809, 
        "next": "https://courses.edx.org/api/course_structure/v0/courses/?page=3", 
        "previous": "https://courses.edx.org/api/course_structure/v0/courses/?page=1",  
        "num_pages": 81, 
        "results": [
            {
                "id": "ANUx/ANU-ASTRO1x/1T2014", 
                "name": "Greatest Unsolved Mysteries of the Universe", 
                "category": "course", 
                "org": "ANUx", 
                "run": "1T2014", 
                "course": "ANU-ASTRO1x", 
                "uri": "https://courses.edx.org/api/course_structure/v0/courses/ANUx/ANU-ASTRO1x/1T2014/", 
                "image_url": "/c4x/ANUx/ANU-ASTRO1x/asset/dome_dashboard.jpg", 
                "start": "2014-03-24T18:30:00Z", 
                "end": null
            }, 
            {
                "id": "ANUx/ANU-ASTRO4x/1T2015", 
                "name": "COSMOLOGY", 
                "category": "course", 
                "org": "ANUx", 
                "run": "1T2015", 
                "course": "ANU-ASTRO4x", 
                "uri": "https://courses.edx.org/api/course_structure/v0/courses/ANUx/ANU-ASTRO4x/1T2015/", 
                "image_url": "/c4x/ANUx/ANU-ASTRO4x/asset/ASTRO4x_dashboard_image.jpeg", 
                "start": "2015-02-03T00:00:00Z", 
                "end": "2015-04-28T23:30:00Z"
            }
            . . .
        ]
    }


.. _

**************************
Get Course Details
**************************

.. .. autoclass:: course_metadata_api.v0.views.CourseDetail

**Example response**

.. code-block:: json

    HTTP 200 OK  
    Vary: Accept   
    Content-Type: text/html; charset=utf-8   
    Allow: GET, HEAD, OPTIONS 
 
    {
        "id": "ANUx/ANU-INDIA1x/1T2014", 
        "name": "Engaging India", 
        "category": "course", 
        "org": "ANUx", 
        "run": "1T2014", 
        "course": "ANU-INDIA1x", 
        "uri": "https://courses.edx.org/api/course_structure/v0/courses/ANUx/ANU-INDIA1x/1T2014/", 
        "image_url": "/c4x/ANUx/ANU-INDIA1x/asset/homepage_course_image.jpg", 
        "start": "2014-04-29T01:00:00Z", 
        "end": "2014-07-21T01:00:00Z"
    }
