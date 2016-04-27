.. _Courses API Courses Resource:

########################################
Courses API Courses Resource
########################################

With the Courses API **Courses** resource, you can complete the
following tasks.

   * - :ref:`Get a list of all courses in a catalog <Get a List of All Courses
     in a Catalog>`
     - GET
     - /api/v1/catalogs/1/courses/

.. contents::
   :local:
   :depth: 1

.. _Get a List of All Courses in a Catalog:

**************************************
Get a List of All Courses in a Catalog
**************************************

The endpoint to get a list of all courses in a catalog is
``/api/v1/catalogs/{id}/courses/``.

=====================
Use Case
=====================

Get a list of all the active courses in a catalog. Active courses are courses
that are currently open for enrollment or that will open for enrollment in the
future.

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

.. _Results:

Results
*******

Parent: ``course``

A list of courses in the catalog.

* key (string): The unique identifier for the course.
* title (string): The title of the course.
* short_description (string): The short description of the course and its
  content.
* full_description (string): The long description of the course and its
  content.
* level_type (ENUM string): ---DESCRIPTION---
* subjects (array): Academic subjects that this course covers. See
  :ref:`Subjects`.
* prerequisites (array): Any courses a learner must complete before enrolling
  in the current course. ---This is in strikethrough text in the Google doc. Is
  it to be deleted?---
* expected_learning_items (array): ---This is in strikethrough text in the
  Google doc. Is it to be deleted?---
* image (array): The About page image for this course. See :ref:`image`.
* video (array): The course About video. See :ref:`Video`.
* owners (array): Institution that offers the course. See :ref:`Organization`.
* sponsors (array): Corporate sponsor for the course. See :ref:`Organization`.
* modified (datetime): The date and time the course was last modified.
* course_runs (array): Information about specific runs of the course. See
  :ref:`Course Runs`.
* marketing_url: ---DESCRIPTION---

.. _Course Runs:

course_runs
============

Parent: ``results``

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
* pacing_type (ENUM string): The pacing of the course. May be **self-paced** or
  **instructor-paced**.
* min_effort (integer): ---Not in Google doc. A different value, "effort", is
  in strikethrough text. Is this to be deleted? ---
* max_effort (integer): ---Not in Google doc. A different value, "effort", is
  in strikethrough text. Is this to be deleted? ---
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

``instructor`` or ``staff``

* key
* name
* title
* bio
* profile_image (array): See :ref:`Image`.

.. _Prerequisites:

Prerequisites
==================

Any courses a learner must complete before enrolling in the current course.

* name (string): ---The name of the prerequisite course. (Not course ID? Full name?)---

.. _Seats:

Seats
=========

* type (string): Audit, verified, professional education
* price
* currency
* upgrade_deadline
* credit_provider
* credit_hours

.. _Subjects:

Subjects
=========

Academic subjects that this course covers.

* name (string): Name of a subject (such as "computer science" or "history".)

**Possible values:**

::

    Architecture
    Art & Culture
    Biology & Life Sciences
    Business & Management
    Chemistry
    Communication
    Computer Science
    Data Analysis & Statistics
    Design
    Economics & Finance
    Education & Teacher Training
    Electronics
    Energy & Earth Sciences
    Engineering
    Environmental Studies
    Ethics
    Food & Nutrition
    Health & Safety
    History
    Humanities
    Language
    Law
    Literature
    Math
    Medicine
    Music
    Philanthropy
    Philosophy & Ethics
    Physics
    Science
    Social Sciences


.. _Video:

Video
=========

``video`` array

* src (string)
* description (string)
* image (array): See :ref:`Image`.

=====================================================
Example Response Showing a Catalog of Select Courses
=====================================================

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
