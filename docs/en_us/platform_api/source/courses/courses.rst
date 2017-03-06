.. _Courses API Courses Resource:

########################################
Courses API Courses Resource
########################################

With the Courses API **Courses** resource, you can complete the
following tasks.

.. contents::
   :local:
   :depth: 1


.. _Get a list of courses:

**********************
Get a List of Courses
**********************

The endpoint to get a list of courses is ``/api/courses/v1/courses/``.

=====================
Use Case
=====================

Get a list of the courses that are visible to a specific user. If a username
is not supplied, an anonymous user is assumed. Users with course staff
permissions can specify other users' usernames.

=====================
Request Format
=====================

GET /api/courses/v1/courses/

Example:

GET /api/courses/v1/courses/?username=anjali


.. _Courses Query Parameters:

=====================
Query Parameters
=====================

* username (optional) - The username of the user for whom the course data is
  being accessed. If the request is made for an anonymous user, username is
  not required. Only users with course staff permissions can specify other
  users' usernames.

* org (optional) - A code for an organization; case-insensitive. Example:
  "HarvardX". If ``org`` is specified, the list of courses includes only
  courses that belong to the specified organization.

* mobile (optional) - If specified, the list of courses includes only courses
  that are designated as ``mobile_available``.


.. _Courses Response Values:

=====================
Response Values
=====================

The following fields are returned with a successful response.
All date/time fields are in ISO 8601 notation.

* effort: A textual description of the weekly hours of effort expected in the
  course.

* end: The date and time that the course ends.

* enrollment_end: The date and time that enrollment ends.

* enrollment_start: The date and time that enrollment begins.

* id: A unique identifier of the course; a serialized representation of the
  opaque key identifying the course.

* media: An object that contains named media items, including the following
  objects.

  * course_image: An image to show for the course.

    * uri: The location of the image.

  * course_video: A video about the course.

    * uri: The location of the video.

* name: The name of the course.

* number: The catalog number of the course.

* org: The name of the organization that owns the course.

* overview: An HTML textual description of the course.

* short_description: A textual description of the course.

* start: The date and time that the course begins.

* start_display: The start date of the course, formatted for reading.

* start_type: Indicates how ``start_display`` was set. Possible values are:

  * "string": Manually set by the course author.
  * "timestamp": Generated from the ``start`` timestamp.
  * "empty": No start date is specified.

* pacing: The type of pacing for this course. Possible values are
  ``instructor`` and ``self``.

* course_id: The course key. This field might be returned but is deprecated.
  You should use ``id`` instead.


==============================================================
Example Response Showing The List of Courses Visible to a User
==============================================================

.. code-block:: json

    {

     "media": {
        "course_image": {
            "uri": "/c4x/edX/example/asset/just_a_test.jpg",
            "name": "Course Image"
        }
      },
      "description": "An example course.",
      "end": "2015-09-19T18:00:00Z",
      "enrollment_end": "2015-07-15T00:00:00Z",
      "enrollment_start": "2015-06-15T00:00:00Z",
      "id": "edX/example/2012_Fall",
      "name": "Example Course",
      "number": "example",
      "org": "edX",
      "start": "2015-07-17T12:00:00Z",
      "start_display": "July 17, 2015",
      "start_type": "timestamp"
    }


.. _Get the details for a course:

*************************
Get Details for a Course
*************************

The endpoint to get the details for a course is
``/api/courses/v1/courses/{course_key}/``.

=====================
Use Case
=====================

Get the details for a course that you specify using a course key.

=====================
Request Format
=====================

GET /api/courses/v1/courses/{course_key}

Example:
GET /api/courses/v1/courses/edX%2FDemoX%2FDemo_Course

=====================
Query Parameters
=====================

* username (optional) - The username of the user for whom the course data is
  being accessed. If the request is made for an anonymous user, username is
  not required. Only users with course staff permissions can specify other
  users' usernames.

=====================
Response Values
=====================

:ref:`Response values<Courses Response Values>` for this endpoint are the same
as those for :ref:`Get a list of courses`.


=========================================================
Example Response Showing Details of a Specified Course
=========================================================


The following example response is returned from this request:

GET /api/courses/v1/courses/edX%2FDemoX%2FDemo_Course


.. code-block:: json

 {

   "effort": null,
   "end": "2015-08-08T00:00:00Z",
   "enrollment_start": "2015-01-01T00:00:00Z",
   "enrollment_end": "2015-05-01T00:00:00Z",
   "id": "edX/DemoX/Demo_Course",
   "media": {
       "course_image":   {
           "uri": "/c4x/edX/DemoX/asset/images_course_image.jpg"
           },
       "course_video": {
           "uri": null
           },
    },
    "name": "edX Demonstration Course",
    "number": "DemoX",
    "org": "edX",
    "short_description": null,
    "start": "2015-02-05T05:00:00Z",
    "start_display": "Feb. 5, 2015",
    "start_type": "timestamp",
    "pacing": "instructor",
    "course_id": "edX/DemoX/Demo_Course",
    "overview": "<p>Include your long course description here.</p>"
 }
