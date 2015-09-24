########################################
Course Structure API Resource
########################################

With the Course Structure API **Course Structure** resource, you can complete
the following tasks.

.. contents::
   :local:
   :depth: 1

.. _Get a List of Courses:

**************************
Get a List of Courses
**************************

.. autoclass:: course_structure_api.v0.views.CourseList

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


.. _Get Course Details:

**************************
Get Course Details
**************************

.. autoclass:: course_structure_api.v0.views.CourseDetail

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

.. _Get the Course Structure:

**************************
Get the Course Structure
**************************

.. .. autoclass:: course_structure_api.v0.views.CourseStructure

**Example response**

.. code-block:: json

    {
        "root": "i4x://ANUx/ANU-INDIA1x/course/1T2014", 
        "blocks": {
            "i4x://ANUx/ANU-INDIA1x/html/834f845ae8b944f1882f14ce6417c9d1": {
                "id": "i4x://ANUx/ANU-
                    INDIA1x/html/834f845ae8b944f1882f14ce6417c9d1", 
                "type": "html", 
                "display_name": "", 
                "graded": false, 
                "format": null, 
                "children": []
            }, 
            "i4x://ANUx/ANU-INDIA1x/html/c3493aaebaba4ab6a0499fbc27ac3b0e": {
                "id": "i4x://ANUx/ANU-
                    INDIA1x/html/c3493aaebaba4ab6a0499fbc27ac3b0e", 
                "type": "problem", 
                "display_name": "Check your learning - Part 1",  
                "graded": true,  
                "format": null, 
                "children": []
            }, 
            "i4x://ANUx/ANU-INDIA1x/sequential/3731eee6a39c473c98ef6a5c3f56c04c": {
                "id": "i4x://ANUx/ANU-
                    INDIA1x/sequential/3731eee6a39c473c98ef6a5c3f56c04c", 
                "type": "sequential", 
                "display_name": "Reflective project", 
                "graded": true, 
                "format": "Reflective Project", 
                "children": [
                    "i4x://ANUx/ANU-
                        INDIA1x/vertical/efe3f47a5bc24894b726c229d6bf5968", 
                    "i4x://ANUx/ANU-
                        INDIA1x/vertical/9106a1b1fad040858bad56fe5d48074e", 
                    "i4x://ANUx/ANU-
                        INDIA1x/vertical/27d2cf635bd44038a1207461b761a63a", 
                    "i4x://ANUx/ANU-
                        INDIA1x/vertical/94b719b765b046e2a811f1c4e4f84e5b"
                ]
            },
            "i4x://ANUx/ANU-INDIA1x/vertical/0a3cd583cb1d4108bfbdaf57c511da3a": {
                "id": "i4x://ANUx/ANU-
                    INDIA1x/vertical/0a3cd583cb1d4108bfbdaf57c511da3a", 
                "type": "vertical", 
                "display_name": "What you need to do this week", 
                "graded": false, 
                "format": null, 
                "children": [
                    "i4x://ANUx/ANU-INDIA1x/html/a20abbba4a0f4a578d96cbdd4b34307b"
                ]
            },
        . . .
        }
    }

.. _Get the Course Grading Policy:

*****************************
Get the Course Grading Policy
*****************************

.. autoclass:: course_structure_api.v0.views.CourseGradingPolicy

**Example response**

.. code-block:: json

    HTTP 200 OK  
    Vary: Accept   
    Content-Type: text/html; charset=utf-8   
    Allow: GET, HEAD, OPTIONS 

    [
        {
            "assignment_type": "Week 1 Survey", 
            "count": 2, 
            "dropped": 1, 
            "weight": 0.03
        }, 
        {
            "assignment_type": "Week 5 Survey", 
            "count": 2, 
            "dropped": 1, 
            "weight": 0.03
        }, 
        {
            "assignment_type": "Reflective Project", 
            "count": 1, 
            "dropped": 0, 
            "weight": 0.2
        },
        . . .
    ]
