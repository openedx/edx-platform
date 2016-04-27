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

.. include:: ../shared/courses_response_values.rst


=======================================================
Example Response Showing a List of Courses in a Catalog
=======================================================

.. include:: ../shared/courses_example_response.rst

