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

The endpoint to get a list of all course catalogs is ``/catalog/v1/catalogs/``.

=====================
Use Case
=====================

Get a list of all the available course catalogs.

=====================
Example Request
=====================

``GET /catalog/v1/catalogs/``

=====================
Response Values
=====================

Responses to GET requests for the edX Course Catalog API frequently contain the
**results** response value. The **results** response value is a variable that
represents the intended object from the GET request. For the ``GET
/catalog/v1/catalogs/`` request, the **results** response value is an array
that lists information about the catalogs that are listed on the current page.

* count (integer): The number of available catalogs.
* next (string): The URL for the next page of results.
* previous (string): The URL for the previous page of results.
* results (array): Information about the current page of catalogs. This array
  includes the following response values.

  * id (integer): The catalog identifier.
  * name (string): The name of the catalog.
  * query (string): The query that the server uses to retrieve catalog
    contents.
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
                "viewers": [
                    "username1", "username2"
                ]
            }
        ]
    }

.. _Get Information about a Specific Catalog:

*****************************************
Get Information about a Specific Catalog
*****************************************

The endpoint to get information about a specific catalog is
``/catalog/v1/catalogs/{id}``.

=====================
Use Case
=====================

Get information about a specific catalog.

=====================
Example Request
=====================

``GET /catalog/v1/catalogs/1/``

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
                "viewers": [
                    "username1", "username2"
                ]
    }

.. _Get a List of All Courses in a Catalog:

**************************************
Get a List of All Courses in a Catalog
**************************************

To get a list of all courses in a catalog, the Course Catalog API consumes the
Courses API. The endpoint is ``/catalog/v1/catalogs/{id}/courses/``.

For more information about the Courses API, see :ref:`Courses API Courses
Resource`.

=====================
Use Case
=====================

Get a list of all the active courses in a specified catalog, along with details
about each course. Active courses are courses that are currently open for
enrollment or that will open for enrollment in the future.

=====================
Example Request
=====================

``GET /catalog/v1/catalogs/1/courses/``

=====================
Response Values
=====================

Responses to GET requests for the edX Course Catalog API frequently contain the
**results** response value. The **results** response value is a variable that
represents the intended object from the GET request. For the ``GET
/catalog/v1/catalogs/{id}/courses/`` request, the **results** response value is
an array that lists information about each individual course in the catalog.

The ``GET /catalog/v1/catalogs/{id}/courses/`` request returns the following
response values.

* count (integer): The number of courses in the catalog.
* next (string): The URL for the next page of results.
* previous (string): The URL for the previous page of results.
* results (array): A list of courses in the catalog.

  The **results** array contains the following response values. Many of these
  values are also arrays. Information about each array is listed below.

  * key (string): The unique identifier for the course.
  * title (string): The title of the course.
  * short_description (string): The short description of the course and its
    content.
  * full_description (string): The long description of the course and its
    content.
  * level_type (ENUM string): The course's level of difficulty. Can be
    ``high_school``, ``introductory``, ``intermediate``, or ``advanced``.
  * subjects (array): Academic subjects that this course covers. See
    :ref:`Subjects`.
  * prerequisites (array): Any courses a learner must complete before enrolling
    in the current course. ---This is in strikethrough text in the Google doc.
    Is it to be deleted?---
  * expected_learning_items (array): ---This is in strikethrough text in the
    Google doc. Is it to be deleted?---
  * image (array): The About page image for this course. See :ref:`image`.
  * video (array): The course About video. See :ref:`Video`.
  * owners (array): Institution that offers the course. See
    :ref:`Organization`.
  * sponsors (array): Corporate sponsor for the course. See
    :ref:`Organization`.
  * modified (datetime): The date and time the course was last modified.
  * course_runs (array): Information about specific runs of the course. See
    :ref:`Course Runs`.
  * marketing_url (string): The URL for the course About page.

.. _Course Runs:

course_runs
============

Parent: ``results``

A list of course runs for each course.

* course
* key (string): The unique identifier for the course.
* title (string): The title of the course.
* short_description (string): The short description of the course and its
  content.
* full_description (string): The long description of the course and its
  content.
* start (datetime): The course start date.
* end (datetime): The course end date.
* enrollment_start (datetime): The course enrollment start date.
* enrollment_end (datetime): The course enrollment end date.
* announcement ---Not in Google doc---
* image (array): See :ref:`Image`.
* video (array): The About video for this course run. See :ref:`Video`.
* seats (array): The available modes for this course. See :ref:`Seats`.
* content_language (string): The language for this course run.
* transcript_languages (array[string]): Languages in which video transcripts
  are available. ---This is in strikethrough text in the Google doc. Is
  it to be deleted?---
* instructors (array): See :ref:`Person`. ---Not in Google doc---
* staff (array): Information about the course staff. See :ref:`Person`.
* pacing_type (ENUM string): The pacing of the course. May be ``self-paced`` or
  ``instructor-paced``.
* min_effort (integer): The minimum number of estimated hours of effort per
  week.
* max_effort (integer): The maximum number of estimated hours of effort per
  week.
* modified (datetime): The date and time the course was last modified.

.. _Image:

image
======

The following ``image`` objects have identical response values.

* ``image`` (parent: ``course``, ``course_runs``, ``video``)
* ``logo_image`` (parent: ``organization``)
* ``profile_image`` (parent: ``person``)

The ``image`` object has the following response values.

* src (string): The URL where the image is located.
* description (string): A description of the image.
* height (integer): The height of the image in pixels.
* width (integer): The width of the image in pixels.

.. _Organization:

organization
==============

The following ``organization`` objects have identical response values.

* ``owners`` (parent: ``results``)
* ``sponsors`` (parent: ``results``)

The ``organization`` object has the following response values.

* key (string): The unique ID for the organization.
* name (string): The name of the organization.
* description (string): A description of the organization.
* logo_image (array): See :ref:`Image`.
* homepage_url (string): The URL of the organization's home page.

.. _Person:

person
=========

The following ``person`` objects have identical response values.

* ``instructor`` (parent: ``course_runs``)
* ``staff`` (parent: ``course_runs``)

The ``person`` object has the following response values.

* key (string): A unique identifier for the instructor or staff member.
* name (string): The first and last name of the instructor or staff member.
* title (string): The official title of the instructor or staff member.
* bio (string): Biographical information about the instructor or staff member.
* profile_image (array): See :ref:`Image`.

.. _Prerequisites:

prerequisites
==================

Parent: ``results``

Any courses a learner must complete before enrolling in the current course.

* name (string): The name of the prerequisite course.

.. _Seats:

seats
=========

Parent: ``course_runs``

* type (string): The course mode or modes that the course offers. Possible
  values are ``audit``, ``credit``, ``honor``, ``professional education``, or
  ``verified``.
* price (string): The cost in USD of a verified certificate, a professional
  education certificate, or academic credit for the course.
* currency (string): The currency in which the course accepts payment. This
  value must be ``USD``.
* upgrade_deadline (string): The deadline for learners to upgrade from the
  audit track to the verified certificate track.
* credit_provider (string): The institution that offers academic credit for
  learners who pass the course.
* credit_hours (integer): The number of credit hours that learners who pass the
  course earn.

.. _Subjects:

subjects
=========

Parent: ``results``

Academic subjects that this course covers.

* name (string): Name of a subject, such as "computer science" or "history".

**Example values:**

::

    Architecture
    Chemistry
    Computer Science
    Economics & Finance
    Health & Safety
    History
    Music
    Physics
    Social Sciences

.. _Video:

video
=========

Parent: ``course``, ``course_runs``

* src (string): URL for the video.
* description (string): Description of the video.
* image (array): See :ref:`Image`.



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


