.. _Course Catalog API Catalogs Resource:

########################################
Course Catalog API Catalogs Resource
########################################

With the Course Catalog API **Catalogs** resource, you can complete the
following tasks.

   * :ref:`Get a list of all available course catalogs <Get a List of All
     Course Catalogs>`
     - GET
     - /api/v1/catalogs/
   * - :ref:`Get information about a specific catalog <Get Information About a
     Specific Catalog>`
     - GET
     - /api/v1/catalogs/1/
   * - :ref:`Get a list of all courses in a catalog <Get a List of All Courses
     in a Catalog>`
     - GET
     - /api/v1/catalogs/1/courses/

.. contents::
   :local:
   :depth: 1

.. _Get a List of All Course Catalogs:

**************************************
Get a List of All Course Catalogs
**************************************

The endpoint to get a list of all course catalogs is ``/api/v1/catalogs/``.

=====================
Use Case
=====================

Get a list of all the available course catalogs.

=====================
Example Request
=====================

``GET /api/v1/catalogs/``

=====================
Response Values
=====================

* count (integer): The number of available catalogs.
* next (string): The URL for the next page of results.
* previous (string): The URL for the previous page of results.
* results (array): Information about one of the available catalogs.

  * id (integer): The catalog identifier.
  * name (string): The name of the catalog.
  * query (string): The query to retrieve catalog contents.
  * courses_count (integer): The number of courses this catalog contains.
  * viewers (array[string]): Usernames of users with explicit access to view
    this catalog.

======================================================
Example Response Showing a List of All Course Catalogs
======================================================

Response Code and Header
**************************

.. code-block:: json

    HTTP 200 OK
    Allow: GET
    Content-Type: application/json
    Vary: Accept

Response Body
**************************

.. code-block:: json

    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 1,
                "name": "All Courses",
                "query": "*:*",
                "courses_count": 18,
                "viewers": []
            }
        ]
    }

.. _Get Information about a Specific Catalog:

*****************************************
Get Information about a Specific Catalog
*****************************************

The endpoint to get information about a specific catalog is
``/api/v1/catalogs/{id}``.

=====================
Use Case
=====================

Get information about a specific catalog.

=====================
Example Request
=====================

``GET /api/v1/catalogs/1/``

=====================
Response Values
=====================

* id (integer): The catalog identifier.
* name (string): The name of the catalog.
* query (string): The query to retrieve catalog contents.
* courses_count (integer): The number of courses this catalog contains.
* viewers (array[string]): Usernames of users with explicit access to view
this catalog.

======================================================
Example Response Showing Information About a Catalog
======================================================

Response Code and Header
**************************

.. code-block:: json

    HTTP 200 OK
    Allow: GET
    Content-Type: application/json
    Vary: Accept

Response Body
**************************

.. code-block:: json

    {
        "id": 1,
        "name": "All Courses",
        "query": "*:*",
        "courses_count": 18,
        "viewers": []
    }

.. _Get a List of All Courses in a Catalog:

**************************************
Get a List of All Courses in a Catalog
**************************************

To get a list of all courses in a catalog, the Course Catalog API consumes the
Courses API. The endpoint is ``/api/v1/catalogs/{id}/courses/``.

For more information about the Courses API, see :ref:`Courses API Courses
Resource`.

=====================
Use Case
=====================

Get a list of all the active courses in a catalog, along with details about
each course. Active courses are courses that are currently open for enrollment
or that will open for enrollment in the future.

=====================
Example Request
=====================

``GET /api/v1/catalogs/1/courses/``

=====================
Response Values
=====================

.. _Course:

Course
*******

* count (integer): The number of courses in the catalog.
* next (string): The URL for the next page of results.
* previous (string): The URL for the previous page of results.
* results (array): See :ref:`Results`.

The ``results`` array contains the response values from the Courses API, including course title, description, run, and start and end date information.

.. include:: ../shared/courses_response_values.rst


=======================================================
Example Response Showing a List of Courses in a Catalog
=======================================================

Response Code and Header
**************************

.. code-block:: json

    HTTP 200 OK
    Allow: GET
    Content-Type: application/json
    Vary: Accept

Response Body
**************************

.. code-block:: json

    {
        "count": 123,
        "next": "https://example.edx.org/api/v1/courses/?offset=60",
        "previous": "https://example.edx.org/api/v1/courses/?offset=20",
        "results": [
            {
                "key": "example_course_key",
                "title": "Title of the Course",
                "short_description": "Short description of course content",
                "full_description": "Longer, more detailed description of course content.",
                "level_type": "Introductory",
                "subjects": [
                    {
                        "name": "Name of subject"
                    }
                ],
                "prerequisites": [],
                "expected_learning_items": [],
                "image": [
                    {
                        "src": "https://example.com/directory/course_image.jpg",
                        "description": "Example image for the Example Title course",
                        "height": "300",
                        "width": "400"
                     }
                ],
                "video": [
                    {
                        "src": "http://www.youtube.com/watch?v=abcdefghijk",
                        "description": null,
                        "image": null
                    }
                ],
                "owners": [
                    {
                        "key": "example_institution_key",
                        "name": "Example Institution",
                        "description": null,
                        "logo_image": [
                            {
                            "src": "https://example.com/directory/institution_logo.jpg",
                            "description": null
                            "height": "200",
                            "width": "200"
                            }
                        ],
                        "homepage_url": null
                    }
                ],
                "sponsors": [],
                "modified": "YYYY-MM-DDTHH:MM:SS.SSSSSSZ",
                "course_runs": [
                    {
                        "course": "course_number",
                        "key": "example_course_key",
                        "title": "Title of the Course",
                        "short_description": "Short description of course content",
                        "full_description": "Longer, more detailed description of course content",
                        "start": "YYYY-MM-DDTHH:MM:SSZ",
                        "end": "YYYY-MM-DDTHH:MM:SSZ",
                        "enrollment_start": "YYYY-MM-DDTHH:MM:SSZ",
                        "enrollment_end": "YYYY-MM-DDTHH:MM:SSZ",
                        "announcement": null,
                        "image": [
                            {
                            "src": "https://example.com/directory/course_image.jpg",
                            "description": null,
                            "height": "200",
                            "width": "300"
                            },
                        ]
                        "video": null,
                        "seats": [
                            {
                            "type": "credit",
                            "price": "100.00",
                            "currency": "USD",
                            "upgrade_deadline": "YYYY-MM-DDTHH:MM:SSZ",
                            "credit_provider": "example institution",
                            "credit_hours": 3
                            }
                        ],
                        "content_language": null,
                        "transcript_languages": [],
                        "instructors": [],
                        "staff": [
                            {
                            "key": "staff_key",
                            "name": "Staff Member Name",
                            "title": "Staff Member Title",
                            "bio": "Example staff member bio.",
                            "profile_image": {
                                "src": "https://example.com/image/staff_member_name.png",
                                "description": null,
                                "height": "150",
                                "width": "150"
                            }
                        ],
                        "pacing_type": "instructor_paced",
                        "min_effort": null,
                        "max_effort": null,
                        "modified": "YYYY-MM-DDTHH:MM:SS.SSSSSSZ"
                    }
                ],
                "marketing_url": "https://example.org/url_for_marketing_materials"
            }
        ]
    }
