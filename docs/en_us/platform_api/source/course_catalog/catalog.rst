########################################
Course Catalog API Catalog Resource
########################################

With the Course Catalog API **Catalog** resource, you can complete the
following tasks.

.. contents::
   :local:
   :depth: 1


.. _Get a List of All Catalogs:

***************************
Get a List of All Catalogs
***************************

.. class enrollment.views.EnrollmentView(**kwargs)[source] (?)

===============
Use Case
===============

Get a list of all catalogs.

===============
Example Request
===============

``GET api/v1/catalogs/``

===============
Response Values
===============

If the request for information about the user is successful, an HTTP 200 “OK”
response is returned.

The HTTP 200 response has the following values.

* count
* next
* previous
* results

  * courses_count
  * id
  * name
  * query
  * viewers

Example response showing a catalog of select courses
****************************************************

.. code-block:: json

    HTTP 200 OK

    {
      "Date": "Wed, 20 Apr 2016 19:45:55 GMT",
      "Content-Encoding": "gzip",
      "Allow": "GET, POST, HEAD, OPTIONS",
      "Server": "nginx/1.8.1",
      "X-Frame-Options": "SAMEORIGIN",
      "Vary": "Accept-Encoding, Accept, Accept-Language, Cookie",
      "Content-Language": "en",
      "Connection": "keep-alive",
      "Content-Type": "application/json",
      "Content-Length": "199"
    }

    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "name": "All MITx and HarvardX Courses",
          "query": "{\r\n  \"query\": {\r\n    \"query_string\": {\r\n      \"query\": \"org:(MITx OR HarvardX)\",\r\n      \"analyze_wildcard\": true\r\n    }\r\n  }\r\n}",
          "courses_count": 0,
          "viewers": []
        }
      ]
    }



.. _Create a New Catalog:

***************************
Create a New Catalog
***************************

.. class enrollment.views.EnrollmentView(**kwargs)[source] (?)

===============
Use Case
===============

Create a new catalog.

===============
Example Request
===============

``POST api/v1/catalogs/``

===============
Parameters
===============

.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - Parameter Name
     - Required
     - Description
     - Parameter Type
     - Data Type
   * - name
     - Yes
     - Catalog name.
     - form
     - string
   * - query
     - Yes
     - Query to retrieve catalog contents.
     - form
     - string
   * - viewers
     - No
     - Usernames of users with explicit access to view this catalog.
     - form
     - string

===============
Response Values
===============

If the request for information about the user is successful, an HTTP "201
CREATED" response is returned.

The HTTP 201 response has the following values.

* courses_count
* id
* name
* query
* viewers

Example response creating a new catalog
***************************************

.. code-block:: json

    HTTP 201 CREATED

    {
      "Date": "Wed, 20 Apr 2016 20:45:09 GMT",
      "Allow": "GET, POST, HEAD, OPTIONS",
      "Server": "nginx/1.8.1",
      "X-Frame-Options": "SAMEORIGIN",
      "Vary": "Accept, Accept-Language, Cookie",
      "Content-Language": "en",
      "Content-Type": "application/json",
      "Connection": "keep-alive",
      "Content-Length": "79"
    }

    {
      "id": 2,
      "name": "example_catalog",
      "query": "example",
      "courses_count": 6,
      "viewers": []
    }





.. _Get Details About a Catalog:

***************************
Get Details About a Catalog
***************************

.. class enrollment.views.EnrollmentView(**kwargs)[source] (?)

===============
Use Case
===============

Get details about a catalog.

===============
Example Request
===============

``GET api/v1/catalogs/{id}``

===============
Parameters
===============

.. list-table::
   :widths: 25 25 50
   :header-rows: 1

   * - Parameter Name
     - Required
     - Description
     - Parameter Type
     - Data Type
   * - ``id``
     - Yes
     - ******DESCRIPTION NEEDED******
     - path
     - string

===============
Response Values
===============

If the request for information about the user is successful...
