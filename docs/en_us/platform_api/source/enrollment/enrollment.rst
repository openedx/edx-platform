##################################################
Enrollment API Module
##################################################

This page contains information on using the Enrollment API to complete
these actions:

* :ref:`Get the user's enrollment status in a course <Get the Users Enrollment Status in a Course>`
* :ref:`Get enrollment details for a course<Get Enrollment Details for a Course>`
* :ref:`View a user's enrollments <View and add to a Users Course Enrollments>`
* :ref:`Enroll a user in a course <View and add to a Users Course Enrollments>`
  

.. _Get the Users Enrollment Status in a Course:

********************************************
Get the User's Enrollment Status in a Course
********************************************

.. autoclass:: enrollment.views.EnrollmentView

**Example response showing the user's enrollment status in a course**

.. code-block:: json

    HTTP 200 OK
    Content-Type: application/json
    Vary: Accept
    Allow: GET, HEAD, OPTIONS

    {
        "created": "2014-11-19T04:06:55Z", 
        "mode": "honor", 
        "is_active": true, 
        "course_details": {
            "course_id": "edX/DemoX/Demo_Course", 
            "enrollment_end": null, 
            "course_modes": [
                {
                    "slug": "honor", 
                    "name": "Honor Code Certificate", 
                    "min_price": 0, 
                    "suggested_prices": [], 
                    "currency": "usd", 
                    "expiration_datetime": null, 
                    "description": null
                }
            ], 
            "enrollment_start": null, 
            "invite_only": false
        }, 
        "user": "staff"
    }

.. _Get Enrollment Details for a Course:

************************************
Get Enrollment Details for a Course
************************************

.. autoclass:: enrollment.views.EnrollmentCourseDetailView

**Example response showing a user's course enrollments**

.. code-block:: json

    HTTP 200 OK
    Content-Type: application/json
    Vary: Accept
    Allow: GET, HEAD, OPTIONS

    {
        "course_id": "edX/DemoX/Demo_Course", 
        "enrollment_end": null, 
        "course_modes": [
            {
                "slug": "honor", 
                "name": "Honor Code Certificate", 
                "min_price": 0, 
                "suggested_prices": [], 
                "currency": "usd", 
                "expiration_datetime": null, 
                "description": null
            }
        ], 
        "enrollment_start": null, 
        "invite_only": false
    }


.. _View and add to a Users Course Enrollments:

*********************************************
View and Add to a User's Course Enrollments
*********************************************

.. autoclass:: enrollment.views.EnrollmentListView


**Example response showing a user's course enrollments**

.. code-block:: json

    HTTP 200 OK
    Content-Type: application/json
    Vary: Accept
    Allow: GET, POST, HEAD, OPTIONS

    [
        {
            "created": "2014-09-19T18:08:37Z", 
            "mode": "honor", 
            "is_active": true, 
            "course_details": {
                "course_id": "edX/DemoX/Demo_Course", 
                "enrollment_end": null, 
                "course_modes": [
                    {
                        "slug": "honor", 
                        "name": "Honor Code Certificate", 
                        "min_price": 0, 
                        "suggested_prices": [], 
                        "currency": "usd", 
                        "expiration_datetime": null, 
                        "description": null
                    }
                ], 
                "enrollment_start": null, 
                "invite_only": false
            }, 
            "user": "honor"
        }, 
        {
            "created": "2014-09-19T18:09:35Z", 
            "mode": "honor", 
            "is_active": true, 
            "course_details": {
                "course_id": "ArbisoftX/BulkyEmail101/2014-15", 
                "enrollment_end": null, 
                "course_modes": [
                    {
                        "slug": "honor", 
                        "name": "Honor Code Certificate", 
                        "min_price": 0, 
                        "suggested_prices": [], 
                        "currency": "usd", 
                        "expiration_datetime": null, 
                        "description": null
                    }
                ], 
                "enrollment_start": "2014-05-01T04:00:00Z", 
                "invite_only": false
            }, 
            "user": "honor"
        }
    ]


**Example post request to enroll the user in a new course**

.. code-block:: json

    {
        “course_details”: {
            “course_id”: “edX/DemoX/Demo_Course”
        }
    }