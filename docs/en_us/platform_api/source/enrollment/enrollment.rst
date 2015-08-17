##################################################
Enrollment API
##################################################

This page contains information on using the Enrollment API to complete
the following actions.

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
        "course_end": "2015-06-30T05:00:00Z", 
        "course_start": "2015-02-05T05:00:00Z", 
        "course_modes": [
            {
                "slug": "honor", 
                "name": "Honor Code Certificate", 
                "min_price": 0, 
                "suggested_prices": [], 
                "currency": "usd", 
                "expiration_datetime": null, 
                "description": null, 
                "sku": null
            }
        ], 
        "enrollment_start": "2015-01-01T05:00:00Z", 
        "enrollment_end": "2015-02-13T05:00:00Z", 
        "invite_only": false, 
        "course_id": "edX/DemoX/Demo_Course"
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
        "course_end": "2015-06-30T05:00:00Z", 
        "course_start": "2015-02-05T05:00:00Z", 
        "course_modes": [
            {
                "slug": "honor", 
                "name": "Honor Code Certificate", 
                "min_price": 0, 
                "suggested_prices": [], 
                "currency": "usd", 
                "expiration_datetime": null, 
                "description": null, 
                "sku": null
            }
        ], 
        "enrollment_start": "2015-01-01T05:00:00Z", 
        "enrollment_end": "2015-02-13T05:00:00Z", 
        "invite_only": false, 
        "course_id": "edX/DemoX/Demo_Course"
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
            "created": "2014-11-19T04:06:55Z", 
            "mode": "honor", 
            "is_active": true, 
            "course_details": {
                "course_end": "2015-06-30T05:00:00Z", 
                "course_start": "2015-02-05T05:00:00Z", 
                "course_modes": [
                    {
                        "slug": "honor", 
                        "name": "Honor Code Certificate", 
                        "min_price": 0, 
                        "suggested_prices": [], 
                        "currency": "usd", 
                        "expiration_datetime": null, 
                        "description": null, 
                        "sku": null
                    }
                ], 
            "enrollment_start": "2015-01-01T05:00:00Z", 
            "enrollment_end": "2015-02-13T05:00:00Z", 
            "invite_only": false, 
            "course_id": "edX/DemoX/Demo_Course"
        }, 
        "user": "staff"
    }
    ]


**Example post request to enroll the user in a new course**

.. code-block:: json

    {
        “course_details”: {
            “course_id”: “edX/DemoX/Demo_Course”
        }
    }