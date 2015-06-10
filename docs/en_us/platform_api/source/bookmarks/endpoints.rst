.. _edX Bookmarks API Endpoints:
 
################################################
Bookmarks API Endpoints
################################################
 
You use the Bookmarks API to add a bookmark to an XBlock, get a bookmark or
list of bookmarks for a course, and delete a bookmark.

The following tasks and endpoints are currently supported.
 
.. list-table::
   :widths: 10 70
   :header-rows: 1
 
   * - To:
     - Use this endpoint:
   * - :ref:`Get a list of bookmarks in reverse chronological order <Get a List of Bookmarks>`
     - GET /api/bookmarks/v1/bookmarks/{course_id}
   * - :ref:`Create a new bookmark <Create a New Bookmark>`
     - POST /api/bookmarks/v1/bookmarks/{course_id}
   * - :ref:`Retrieve a bookmark <Retrieve a Bookmark>`
     - GET /api/bookmarks/v0/bookmarks/{username},{usage_id}/
   * - :ref:`Delete a bookmark <Delete a Bookmark>`
     - DELETE /api/bookmarks/v0/bookmarks/{username},{usage_id}/

