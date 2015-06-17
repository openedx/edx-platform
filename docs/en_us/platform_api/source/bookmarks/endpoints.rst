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
   * - :ref:`Get a list of bookmarks in reverse chronological order <Get List or Create Bookmarks>`
     - GET /api/bookmarks/v1/bookmarks/?course_id={course_id1}&fields=display_name,path
   * - :ref:`Create a new bookmark <Get List or Create Bookmarks>`
     - POST /api/bookmarks/v1/bookmarks/
   * - :ref:`Retrieve a bookmark <Retrieve or Delete a Bookmark>`
     - GET /api/bookmarks/v1/bookmarks/{username},{usage_id}/?fields=display_name,path
   * - :ref:`Delete a bookmark <Retrieve or Delete a Bookmark>`
     - DELETE /api/bookmarks/v1/bookmarks/{username},{usage_id}/